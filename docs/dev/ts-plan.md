# TypeScript Backend Implementation Plan

Status: implemented (steps 1-5 done). TypeScript is the 8th backend and passes
7/7 benchmarks via `deno compile`. Remaining follow-ups: bigint decision for
large-int fidelity (trap #1), format-spec completeness, and `deno check`-clean
type annotations (return-type upgrade for inferred container types). Int is
currently `number` (float64) per the settled decision; all 7 benchmark values
stay below 2**53 so none diverge.

This plan describes adding TypeScript as an 8th target backend, framed as a
diff from the existing Go backend (`src/multigen/backends/go/`), which it most
closely resembles in structure.

## 0. Decisions baked in

| Decision | Choice | Rationale |
|---|---|---|
| Build tool | Deno (`deno compile` -> binary, `deno check` -> typecheck) | Runs `.ts` directly (no separate tsc/emit step), produces a standalone binary so the `AbstractBuilder`/benchmark model (compile-time, binary-size, execute-time) maps 1:1 to Go. Bun is a drop-in alt; tsc+node needs two steps and emits no binary. |
| dict -> `Map<K,V>`, not object literal | `Map` preserves key types, insertion order, `.size`, non-string keys | Object literals stringify keys and only key on string/number -- unfaithful to Python dict. |
| set -> `Set<T>`, list -> `T[]` | native | direct, idiomatic |
| Generators | Eager collection first (mirror Go's `__mgen_result` accumulator) | Keeps parity with existing `IRYield`/`is_generator` infra and the other 7 backends. Native `function*`/`yield`/`yield*` is a v2 win TS uniquely enables -- note, don't build yet. |
| Naming | Preserve `snake_case` (no CamelCase transform) | TS doesn't need Go's capitalization-for-export rule. This removes code vs Go (`_to_camel_case` calls drop out). |
| No `interface{}` fallback | use `any` / `unknown` | TS equivalent |

Container choice is the one place generated code diverges meaningfully from
"looks hand-written" -- `Map`/`Set` are correct but slightly less idiomatic
than object literals. Keep correctness.

## 1. File manifest

New package `src/multigen/backends/typescript/` (mirror `go/`):

| File | Source | Change level |
|---|---|---|
| `__init__.py` | copy `go/__init__.py` | trivial |
| `backend.py` | copy `go/backend.py` | s/Go/TypeScript/, `.ts` ext, `get_name()` -> "typescript" |
| `factory.py` | copy `go/factory.py` | rewrite 4 methods for TS syntax |
| `containers.py` | copy `go/containers.py` | rewrite type strings (`T[]`, `Map`, `Set`) |
| `builder.py` | copy `go/builder.py` | rewrite `compile_direct` for `deno compile` |
| `emitter.py` | copy `go/emitter.py` | s/Go/TS/ only |
| `type_inference.py` | copy `go/type_inference.py` | rewrite `_format_*` strings |
| `converter.py` | copy `go/converter.py` (~2291 lines) | the real work -- type_map, operators, statement emitters |
| `runtime/multigen_ts_runtime.ts` | new | semantic shims (see section 6) |

Edits to existing files: `registry.py`, `preferences.py`, `scripts/benchmark.py`,
new `tests/test_backend_typescript_*.py`.

## 2. Trivial files

`backend.py` -- mechanical rename:

```python
class TypeScriptBackend(LanguageBackend):
    def get_name(self) -> str: return "typescript"
    def get_file_extension(self) -> str: return ".ts"
    def get_factory(self) -> AbstractFactory: return TypeScriptFactory()
    def get_emitter(self) -> AbstractEmitter: return TypeScriptEmitter(self.preferences)
    def get_builder(self) -> AbstractBuilder: return TypeScriptBuilder()
    def get_container_system(self) -> AbstractContainerSystem: return TypeScriptContainerSystem()
    def get_optimizer(self) -> AbstractOptimizer:  # NoOpOptimizer -- deno/tsc handles opt
        ...
```

`emitter.py` -- identical to Go's except it constructs
`MultiGenPythonToTypeScriptConverter` and `map_python_type` falls back to `"any"`.

`factory.py` -- 4 methods:

```python
def create_variable(self, name, type_name, value=None):
    return f"let {name}: {type_name} = {value}" if value is not None else f"let {name}: {type_name}"
def create_function_signature(self, name, params, return_type):
    ps = ", ".join(f"{n}: {t}" for n, t in params)
    rt = return_type if return_type else "void"
    return f"function {name}({ps}): {rt}"
def create_comment(self, text): ...  # // same as Go
def create_include(self, library):
    return f'import {{ {library} }} from "./multigen_ts_runtime";'
```

`containers.py`:

```python
def get_list_type(self, e): return f"{e}[]"
def get_dict_type(self, k, v): return f"Map<{k}, {v}>"
def get_set_type(self, e): return f"Set<{e}>"
def get_required_imports(self): return []
```

`type_inference.py` -- same structure as Go's; only the `_format_*` return
strings change (`f"{e}[]"`, `f"Map<{k}, {v}>"`, `f"Set<{e}>"`), and
method-return inference maps `split -> string[]`, etc. Defaults `[]int` ->
`number[]`, `map[int]int` -> `Map<number, number>`.

## 3. builder.py -- the build-tool diff

```python
class TypeScriptBuilder(AbstractBuilder):
    def get_build_filename(self) -> str:
        return "deno.json"
    def generate_build_file(self, source_files, target_name) -> str:
        return '{\n  "compilerOptions": {"strict": true}\n}\n'
    def compile_direct(self, source_file, output_dir, **kwargs) -> bool:
        paths = self._resolve_paths(source_file, output_dir)
        # copy runtime next to source so the relative import resolves
        runtime_dir = self._get_runtime_dir()
        if runtime_dir:
            shutil.copy2(runtime_dir / "multigen_ts_runtime.ts",
                         paths.source_path.parent / "multigen_ts_runtime.ts")
        cmd = ["deno", "compile", "--no-check", "-o",
               str(paths.executable_path), str(paths.source_path)]
        return self._run_command(cmd).success
    def get_compile_flags(self) -> list[str]:
        return []
```

Add a `deno --version` availability check (mirror how other optional toolchains
are probed) so the registry/tests skip cleanly when Deno is absent -- same
pattern as ghc/ocaml in the benchmark runner.

## 4. converter.py -- what actually changes

Copy the whole file, then make these targeted edits. The control-flow
scaffolding (`_convert_module`, statement dispatch, nested-subscript analysis,
unused-var detection, pre-inference passes) transfers unchanged in structure.

### 4a. type_map (constructor)

```python
self.type_map = {
    "int": "number", "float": "number", "bool": "boolean", "str": "string",
    "list": "number[]", "dict": "Map<number, number>", "set": "Set<number>",
    "void": "void", "None": "void",
}
self.exception_map = {  # all map to runtime classes
    "ValueError": "ValueError", "TypeError": "TypeError",
    "KeyError": "KeyError", "IndexError": "IndexError",
    "RuntimeError": "RuntimeError", "ZeroDivisionError": "ZeroDivisionError",
}
```

### 4b. Module preamble

`_convert_module`: replace `package main` + Go import with:

```python
parts.append('import * as mg from "./multigen_ts_runtime";')
```

Keep an entry point. Python convention: emit a trailing `main();` call if a
`main` function exists (instead of Go's implicit `func main`).

### 4c. Naming

Delete `_to_camel_case`/`_to_go_method_name` usages; emit names verbatim. This
deletes code from the class/method/constructor converters.

### 4d. Classes

`_convert_class`/`_convert_constructor`/`_convert_method`: Go structs -> TS `class`:

```text
struct fields ->   field: type;  inside class body
constructor   ->   constructor(params) { this.x = ...; }
methods       ->   methodName(params): ret { ... }
self.attr     ->   this.attr   (replaces obj.Attr)
```

This collapses Go's separate `New<Class>` constructor + receiver methods +
`obj`-rewriting (`_convert_method_*` family) into a single `class` block -- net
simplification. The `_convert_method_expression` `self` -> `obj.Attr` rewrite
becomes `self` -> `this.attr`.

### 4e. Operators -- the semantic-correctness core

```python
# BinOp:
ast.Pow       -> f"({l} ** {r})"          # native, unlike Go's math.Pow
ast.FloorDiv  -> f"mg.floorDiv({l}, {r})" # NOT Go's plain '/'  (see gotcha)
ast.Mod       -> f"mg.pyMod({l}, {r})"    # Python modulo semantics
ast.Div       -> f"({l} / {r})"           # true division (float)
# AugAssign //= , %=  -> expand to  x = mg.floorDiv(x, r)  /  x = mg.pyMod(x, r)
```

### 4f. Builtins

(`_convert_call` / method-context call): map to runtime, drop Go generics syntax:

```python
len(x)   -> "x.length" for arrays/strings, "x.size" for Map/Set  (type-driven, like Go)
range()  -> "mg.range(...)"
print()  -> "mg.print(...)"
str/int/float/bool -> mg.toStr/toInt/toFloat/toBool
min/max/sum/abs    -> mg.min/max/sum/abs  (no [T] type params)
```

### 4g. String methods

`upper -> toUpperCase()`, `lower -> toLowerCase()`, `strip -> mg.strip()`
(JS `trim` differs on which chars / arg form), `split -> mg.split()`,
`replace -> .replaceAll()`, `find -> mg.find()`.

### 4h. Generators

Keep Go's exact strategy: inject `let __mgen_result: T[] = [];`, `yield x` ->
`__mgen_result.push(x)`, `yield from` -> `.push(...)` / range loop,
`return __mgen_result`. The `is_generator` detection and
`_get_generator_element_type` carry over verbatim.

### 4i. try/except, raise, with

Structurally simpler than Go (no defer/recover dance):

```python
try/except -> try { } catch (e) { if (e instanceof ValueError) {...} }
raise X(m) -> throw new mg.ValueError(m)
with open(f) as fh -> const fh = mg.open(path, mode); try { ... } finally { fh.close(); }
```

This replaces the most complex Go method (`_convert_try`, ~110 lines of
anonymous-func/recover generation) with a much shorter native try/catch emitter.

## 5. Registration -- exact diffs

`registry.py` (after the LLVM block, line ~97):

```python
        # Try to register TypeScript backend
        try:
            from .typescript.backend import TypeScriptBackend
            self.register_backend("typescript", TypeScriptBackend)
        except ImportError:
            pass
```

`preferences.py` -- add `TypeScriptPreferences(BackendPreferences)` (copy
`GoPreferences` shape; keys like `target: "deno"`, `strict: True`,
`module_system: "esm"`, `container_dict: "map"`) and add
`"typescript": TypeScriptPreferences` to `_preferences_map` (line ~280).

`scripts/benchmark.py` -- 3 edits:

- ext map (line ~132): `"typescript": ".ts"`
- runtime copy (line ~84 branch): copy `multigen_ts_runtime.ts` beside source
- compile branch (line ~295): `["deno", "compile", "--no-check", "-o", exe, source]`

## 6. runtime/multigen_ts_runtime.ts -- the semantic shims

Small but non-empty (the gotchas that "just transpiling" gets wrong):

```typescript
export function floorDiv(a: number, b: number): number { return Math.floor(a / b); }
export function pyMod(a: number, b: number): number { return ((a % b) + b) % b; } // Python sign
export function* range(a: number, b?: number, step = 1): Generator<number> { ... }
export function print(...xs: unknown[]): void { console.log(xs.map(pyStr).join(" ")); }
export function strip(s: string, chars?: string): string { ... }   // Python strip semantics
export function split(s: string, sep?: string): string[] { ... }   // empty/whitespace differ from JS
export function toStr/toInt/toFloat/toBool(...): ...
export function sum/min/max/abs(...): ...
export class ValueError extends Error {}  // + TypeError, KeyError, IndexError, RuntimeError, ZeroDivisionError
```

## 7. Tests

Add per-feature files mirroring the Go suite (each instantiates the converter
and asserts on emitted strings -- no toolchain needed, so they run in CI
without Deno):
`test_backend_typescript_{basics,oop,comprehensions,augassign,stringmethods,builtins,controlflow,integration}.py`.

Plus update `tests/test_backends.py`: `expected_backends` set and the
`parametrize` lists (currently `{"c","rust","go","cpp"}`, so TS joins the
parametrized smoke tests there).

## 8. The 4 correctness traps

1. number is float64 -- Python `int` is arbitrary-precision. `fibonacci`/`matmul`
   overflow at 2^53. Decision needed: emit `bigint` for int-typed values
   (faithful, viral through the type system) or accept divergence on large-int
   benchmarks. This is the biggest open question and affects how many benchmarks
   pass.
2. `//` and `%` -- handled by `floorDiv`/`pyMod` above; the trap is forgetting
   and emitting JS `/`/`%` (wrong for negatives). Go got away with plain `/`
   because Go int division already truncates; you cannot copy that line.
3. Truthiness -- Python `if xs:` (empty list falsy) vs JS (`[]` truthy). Where
   the analyzer knows a test is a container, wrap in `mg.truthy(...)` or
   `.length`.
4. dict iteration / `.size` vs `.length` -- `len()` must be type-driven
   (`.size` for Map/Set, `.length` for array/string) exactly as Go's `len`
   already branches on inferred type.

## 9. Effort & sequencing

~1,500-2,200 lines, lowest of any backend added. Suggested order:

1. Skeleton (files 2-3) + registration -> backend appears in
   `mgen --target typescript`, emits garbage. (~half day)
2. converter.py core: functions, operators, builtins, control flow -> simple
   benchmarks pass (fibonacci modulo the int-size decision). (bulk)
3. Classes, comprehensions, strings, generators, try/with.
4. Runtime shims + builder + benchmark wiring -> end-to-end compile/run.
5. Tests; then the int-precision decision against the benchmark suite.

## Open question

`bigint` vs `number` for Python `int` (trap #1) shapes the converter's type
handling and should be settled before step 2.
