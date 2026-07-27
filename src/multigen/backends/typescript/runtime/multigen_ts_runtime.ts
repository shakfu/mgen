// MultiGen TypeScript runtime.
//
// Semantic shims for Python behaviors that plain transpilation gets wrong:
// floor division, modulo sign, str/split/strip semantics, truthiness, and
// Python-style stringification. Python `int` is represented as `number`
// (float64) -- faithful below 2**53. See docs/dev/ts-plan.md trap #1.

// ---------------------------------------------------------------------------
// Numeric semantics
// ---------------------------------------------------------------------------

export function floorDiv(a: number, b: number): number {
  return Math.floor(a / b);
}

// Python modulo: result takes the sign of the divisor.
export function pyMod(a: number, b: number): number {
  return ((a % b) + b) % b;
}

export function min(...xs: unknown[]): number {
  const items = xs.length === 1 && Array.isArray(xs[0]) ? (xs[0] as number[]) : (xs as number[]);
  return Math.min(...items);
}

export function max(...xs: unknown[]): number {
  const items = xs.length === 1 && Array.isArray(xs[0]) ? (xs[0] as number[]) : (xs as number[]);
  return Math.max(...items);
}

export function sum(xs: Iterable<number>): number {
  let total = 0;
  for (const x of xs) total += x;
  return total;
}

export function abs(x: number): number {
  return Math.abs(x);
}

// ---------------------------------------------------------------------------
// range
// ---------------------------------------------------------------------------

export function range(a: number, b?: number, step = 1): number[] {
  let start: number;
  let stop: number;
  if (b === undefined) {
    start = 0;
    stop = a;
  } else {
    start = a;
    stop = b;
  }
  const out: number[] = [];
  if (step > 0) {
    for (let i = start; i < stop; i += step) out.push(i);
  } else if (step < 0) {
    for (let i = start; i > stop; i += step) out.push(i);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Truthiness and conversions
// ---------------------------------------------------------------------------

export function truthy(x: unknown): boolean {
  if (x === null || x === undefined || x === false) return false;
  if (typeof x === "number") return x !== 0;
  if (typeof x === "string") return x.length !== 0;
  if (Array.isArray(x)) return x.length !== 0;
  if (x instanceof Map || x instanceof Set) return x.size !== 0;
  return true;
}

export function toBool(x: unknown): boolean {
  return truthy(x);
}

export function toInt(x: unknown): number {
  if (typeof x === "boolean") return x ? 1 : 0;
  return Math.trunc(Number(x));
}

export function toFloat(x: unknown): number {
  return Number(x);
}

export function toStr(x: unknown): string {
  return pyStr(x);
}

// Python-style stringification.
export function pyStr(x: unknown): string {
  if (x === null || x === undefined) return "None";
  if (typeof x === "boolean") return x ? "True" : "False";
  if (typeof x === "string") return x;
  if (Array.isArray(x)) return "[" + x.map(pyRepr).join(", ") + "]";
  if (x instanceof Set) return "{" + [...x].map(pyRepr).join(", ") + "}";
  if (x instanceof Map) {
    return "{" + [...x.entries()].map(([k, v]) => `${pyRepr(k)}: ${pyRepr(v)}`).join(", ") + "}";
  }
  return String(x);
}

function pyRepr(x: unknown): string {
  if (typeof x === "string") return `'${x}'`;
  return pyStr(x);
}

// ---------------------------------------------------------------------------
// print
// ---------------------------------------------------------------------------

export function print(...xs: unknown[]): void {
  console.log(xs.map(pyStr).join(" "));
}

// ---------------------------------------------------------------------------
// String operations (Python semantics)
// ---------------------------------------------------------------------------

export function strip(s: string, chars?: string): string {
  if (chars === undefined) return s.trim();
  let start = 0;
  let end = s.length;
  while (start < end && chars.includes(s[start])) start++;
  while (end > start && chars.includes(s[end - 1])) end--;
  return s.slice(start, end);
}

// Python str.split(): no arg splits on runs of whitespace and drops empties.
export function split(s: string, sep?: string): string[] {
  if (sep === undefined) {
    const trimmed = s.trim();
    return trimmed.length === 0 ? [] : trimmed.split(/\s+/);
  }
  return s.split(sep);
}

// ---------------------------------------------------------------------------
// Builtins
// ---------------------------------------------------------------------------

export function any(xs: Iterable<unknown>): boolean {
  for (const x of xs) if (truthy(x)) return true;
  return false;
}

export function all(xs: Iterable<unknown>): boolean {
  for (const x of xs) if (!truthy(x)) return false;
  return true;
}

export function sorted<T>(xs: Iterable<T>): T[] {
  return [...xs].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

export function enumerate<T>(xs: Iterable<T>, start = 0): [number, T][] {
  const out: [number, T][] = [];
  let i = start;
  for (const x of xs) out.push([i++, x]);
  return out;
}

export function zip<T>(...arrays: T[][]): T[][] {
  const n = Math.min(...arrays.map((a) => a.length));
  const out: T[][] = [];
  for (let i = 0; i < n; i++) out.push(arrays.map((a) => a[i]));
  return out;
}

export function assert_(cond: unknown, msg = "assertion failed"): void {
  if (!truthy(cond)) throw new Error(msg);
}

// Minimal Python-format-spec support (enough for common f-string specs).
export function format(value: unknown, spec: string): string {
  if (typeof value === "number") {
    const m = spec.match(/\.(\d+)f/);
    if (m) return value.toFixed(Number(m[1]));
  }
  return pyStr(value);
}

// ---------------------------------------------------------------------------
// Exceptions
// ---------------------------------------------------------------------------

export class ValueError extends Error {}
export class TypeError_ extends Error {}
export { TypeError_ as TypeError };
export class KeyError extends Error {}
export class IndexError extends Error {}
export class RuntimeError extends Error {}
export class ZeroDivisionError extends Error {}
