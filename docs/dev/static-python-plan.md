# Static Python Subset Plan

## Recommended Direction

Evolve the existing `StaticPythonSubsetValidator` into a profile-driven static
validator rather than creating a separate validation framework.

Separate two concepts:

- **Feature capability**: what a construct means and whether a backend can
  translate it.
- **Profile policy**: whether that construct is accepted, warned about, or
  rejected.

A feature may therefore be supported experimentally without being accepted by
the strict static profile.

## Phase 1: Define The Contract

Define an initial `strict-static` profile.

Accept initially:

- Typed function parameters and return values
- Typed local variables
- Primitive values: `int`, `float`, `bool`, `str`, and `None`
- Homogeneous lists, dictionaries, and sets
- `if`, `for range(...)`, and restricted `while`
- Function calls with statically known signatures
- Deterministic local mutation
- Basic comprehensions

Reject initially:

- `eval`, `exec`, `compile`, and dynamic imports
- Reflection and arbitrary attribute access
- Monkey patching
- Unannotated public parameters and globals
- Mixed-type containers
- Inconsistent variable reassignment
- Generators and `yield` unless explicitly enabled
- Exceptions and context managers unless their semantics are modeled
- Unsupported imports and external runtime dependencies
- Ambiguous or low-confidence type inference

Document this contract in `docs/supported_syntax.md`.

## Phase 2: Add Profile And Diagnostic Models

Add a module such as `src/multigen/frontend/static_profile.py` containing:

- `StaticProfile`
- `FeatureSpec`
- `Diagnostic`
- `DiagnosticSeverity`
- `SourceSpan`
- `ValidationReport`

Each diagnostic should include:

- Stable rule ID, for example `STATIC.UNANNOTATED_PARAMETER`
- Severity
- Human-readable message
- Source line and column
- End position
- AST node type
- Profile name
- Suggested remediation
- Optional inferred type or supporting evidence

Retain compatibility accessors for the current string-based `ValidationResult`
API.

## Phase 3: Refactor The Existing Validator

Refactor `src/multigen/frontend/subset_validator.py` to:

- Replace overlapping AST-node rule matching with a deterministic
  `ast.NodeVisitor`.
- Ensure each construct is classified once.
- Remove shared mutable state such as `last_validation_error`.
- Keep validation state local to each call.
- Preserve `validate_code`, `validate_file`, and
  `generate_subset_report`.
- Add profile selection to validation methods.
- Treat unknown AST constructs as errors in `strict-static`.

This should also address the currently unused `validation_cache`.

## Phase 4: Integrate Existing Type Analysis

Use the existing analysis components as one validation pipeline:

1. Parse source once.
2. Run subset/profile validation.
3. Run `ASTAnalyzer`.
4. Run flow-sensitive type inference.
5. Run `PythonConstraintChecker`.
6. Merge all diagnostics.
7. Apply profile-specific policies.

Validate:

- Parameter and return annotations
- Definite assignment
- Assignment compatibility
- Branch type joins
- Container element consistency
- Function call signatures
- Unknown and low-confidence types
- Global variable restrictions
- Mutation constraints

Distinguish definitely valid, definitely invalid, and unknown results. The
`strict-static` profile should reject unknown or low-confidence results.

## Phase 5: Define Backend Profiles

Add profiles for:

```text
strict-static
portable
c
cpp
rust
go
haskell
ocaml
llvm
typescript
```

Start with `strict-static`, `portable`, and backend-specific profiles.

Each profile should specify:

- Accepted syntax
- Accepted types
- Mutation and ownership rules
- Exception behavior
- Runtime requirements
- Unsupported constructs
- Known semantic deviations

The selected backend must not silently broaden the language accepted by
`strict-static`.

## Phase 6: Integrate With The Pipeline

Add profile selection to `PipelineConfig`:

```python
validation_profile: str = "portable"
```

Suggested semantics:

- `portable`: common subset across selected targets
- `strict-static`: conservative statically translatable subset
- Backend-specific profiles: target-specific capabilities

Update pipeline Phase 1 to:

1. Parse once.
2. Validate against the selected profile.
3. Store the structured report in `ValidationPhaseResult`.
4. Stop before memory safety, formal verification, or generation when blocking
   diagnostics exist.
5. Pass the same AST and analysis context to later phases.

Extend `src/multigen/pipeline_types.py` with structured validation data while
preserving existing fields.

## Phase 7: Upgrade The CLI

Extend `multigen check` with:

```bash
multigen check program.py --profile strict-static
multigen check program.py --profile portable --format json
multigen check program.py --target rust
multigen check program.py --warnings-as-errors
multigen check --report --profile strict-static
```

Add:

- `--profile`
- `--target` as a profile shortcut
- `--format text|json`
- `--warnings-as-errors`
- Stable exit codes
- Multiple input file support
- Correct report-only behavior
- No false success for invalid or missing files

`--report` should describe a profile without implying that an input file was
validated.

## Phase 8: Add Tests

Add tests for profile acceptance:

- Valid typed functions
- Valid control flow
- Valid homogeneous containers
- Valid basic comprehensions

Add tests for profile rejection:

- Dynamic execution
- Reflection
- Unannotated parameters
- Mixed-type containers
- Incompatible reassignment
- Unsupported exceptions and generators
- Unknown AST nodes

Add diagnostic tests for:

- Stable IDs
- Exact source spans
- Multiple diagnostics
- Deterministic ordering
- JSON serialization

Add integration tests for:

- Pipeline early exit
- `ValidationPhaseResult` contents
- Profile-specific backend behavior
- `--format json`
- `--warnings-as-errors`
- Multi-file CLI validation
- `--report`

Extend the existing frontend, CLI, pipeline, and type-inference tests rather
than creating a parallel test hierarchy.

## Phase 9: Synchronize Documentation

Make `docs/supported_syntax.md` the user-facing contract.

Add generated tables showing:

- Profile
- Feature
- Accepted, warned, or rejected status
- Backend availability
- Semantic caveats
- Required runtime support

Update:

- `README.md`
- `docs/guide/quickstart.md`
- `docs/api/frontend.md`
- `docs/api/pipeline.md`

Prefer generating feature tables from the formal registry to avoid divergent
manual feature lists.

## Phase 10: CI And Release Policy

Add CI jobs for:

- Python 3.13 with LLVM enabled
- Python 3.14 with LLVM skipped
- Strict static profile validation
- Portable profile validation
- All supported backend profiles
- JSON diagnostics
- Clean installation and package build

Require that:

- Unsupported constructs never silently reach a backend.
- Strict profile tests pass.
- Documentation feature tables stay synchronized.
- Generated diagnostics remain backward compatible.

## Suggested MVP

Implement in this order:

1. Define `strict-static` rules.
2. Add structured diagnostics.
3. Refactor `StaticPythonSubsetValidator` into a deterministic visitor.
4. Integrate type inference.
5. Add `--profile strict-static`.
6. Add accepted and rejected fixture tests.
7. Update pipeline results and documentation.
8. Add backend-specific profiles afterward.

## Settled Design Decision

The question was whether exceptions, generators, and context managers should
remain excluded from `strict-static`. It was settled by executing generated C
against CPython rather than by preference, because the criterion in Phase 1 was
"unless their semantics are modeled" and only measurement can answer that.

| Construct | Measurement | Decision |
| --- | --- | --- |
| Generators, `yield from` | A generator can be defined but not consumed. The C backend refuses `for v in counter(5)`, and the frontend's own control-flow rule rejects iterating a call. | Excluded from `strict-static` |
| Exceptions | An explicit `raise` is caught and `finally` runs, both matching CPython. But no operation raises: `10 // 0` inside a `try` dies of SIGFPE where Python returns from the handler. | Excluded from `strict-static` |
| Context managers | The basic `with ... as ...` form executes and agrees with CPython. | Kept in `strict-static` |

Excluding context managers as well would have been caution without evidence,
which is the habit that produced the stale statuses in the first place.

Two defects surfaced while measuring, both now fixed:

- `multigen_python_ops.h` defined a second `MGEN_TRY`/`MGEN_END_TRY` family that
  shared names with the setjmp-based one in `multigen_error_handling.h` but had
  a different shape. Generated files include both, this one last, so its
  definitions won and then composed with the other header's `MGEN_CATCH`. Every
  generated program containing `try`/`except` failed to compile while the
  pipeline reported success. The duplicate family was unused and is gone.
- The capability probes for generators and `yield from` defined a generator
  without consuming one, so the matrix recorded `ok` for a feature with no
  end-to-end path. Both probes now consume, and the matrix records `refuses`
  for the C backend.

The remaining gap is that a probe measures emission, not compilation: a backend
can emit source the matrix calls `ok` that no compiler accepts. Extending the
matrix to compile and run each probe would close it.
