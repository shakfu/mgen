# Getting Started with MGen

**Welcome to MGen!** This tutorial will guide you through installing MGen and creating your first program in multiple languages.

MGen translates Python code to C, C++, Rust, Go, Haskell, and OCaml - allowing you to write in Python and get the performance and ecosystem benefits of compiled languages.

---

## Table of Contents

1. [Installation](#installation)
2. [Your First Program](#your-first-program)
3. [Understanding the Workflow](#understanding-the-workflow)
4. [Language-Specific Guides](#language-specific-guides)
5. [Common Patterns](#common-patterns)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Installation

### Prerequisites

**Python**: MGen requires Python 3.9 or later.

```bash
python --version  # Should be 3.9+
```

**Target Language Compilers** (optional, install only what you need):
- **C**: `gcc` or `clang`
- **C++**: `g++` or `clang++`
- **Rust**: `rustc` and `cargo` (install from [rustup.rs](https://rustup.rs))
- **Go**: `go` compiler (install from [golang.org](https://golang.org))
- **Haskell**: `ghc` (install from [haskell.org](https://www.haskell.org))
- **OCaml**: `ocamlc` (install from [ocaml.org](https://ocaml.org))

### Install MGen

```bash
# Clone the repository
git clone https://github.com/yourusername/mgen.git
cd mgen

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Verify Installation

```bash
# Check MGen is installed
mgen --help

# List available backends
mgen backends
```

You should see output listing all 6 available backends: `c`, `cpp`, `rust`, `go`, `haskell`, `ocaml`.

---

## Your First Program

Let's create a simple "Hello, World!" program and translate it to multiple languages.

### Step 1: Write Python Code

Create a file called `hello.py`:

```python
"""Hello World in MGen."""

def greet(name: str) -> str:
    """Return a greeting message."""
    return "Hello, " + name + "!"

def main() -> int:
    """Main function."""
    message: str = greet("World")
    print(message)
    return 0
```

**Key Points**:
- ✅ Use type annotations (`: str`, `-> int`, `message: str`)
- ✅ Include a `main()` function
- ✅ Return `int` from `main()` (0 for success)
- ✅ Declare variables with types (e.g., `message: str`)

### Step 2: Convert to Target Language

Choose your target language and convert:

```bash
# Convert to C
mgen --target c convert hello.py

# Convert to C++
mgen --target cpp convert hello.py

# Convert to Rust
mgen --target rust convert hello.py

# Convert to Go
mgen --target go convert hello.py

# Convert to Haskell
mgen --target haskell convert hello.py

# Convert to OCaml
mgen --target ocaml convert hello.py
```

The generated code will be in `build/src/hello.{c,cpp,rs,go,hs,ml}`.

### Step 3: Build and Run

**Option A: Let MGen compile for you**

```bash
# Build directly (creates executable)
mgen --target cpp build hello.py
./build/hello

# Or generate Makefile
mgen --target cpp build hello.py -m
cd build && make && ./hello
```

**Option B: Compile manually**

```bash
# C
gcc build/src/hello.c -o build/hello
./build/hello

# C++
g++ build/src/hello.cpp -o build/hello
./build/hello

# Rust
cd build/src && rustc hello.rs && ./hello

# Go
cd build/src && go build hello.go && ./hello

# Haskell
cd build/src && ghc hello.hs && ./hello

# OCaml
cd build/src && ocamlc hello.ml -o hello && ./hello
```

**Output**: All versions should print:
```
Hello, World!
```

🎉 **Congratulations!** You've just translated Python to 6 different languages!

---

## Understanding the Workflow

### Type Inference (NEW!)

**MGen now automatically infers types for local variables!** You no longer need to annotate every variable:

```python
def example() -> int:
    # Type annotations are OPTIONAL for local variables!
    numbers = []           # Inferred as list[int] from append()
    numbers.append(10)

    result = len(numbers)  # Inferred as int from len() return type
    x = 5                  # Inferred as int from literal

    return result + x
```

**What's inferred:**
- ✅ Local variables from literals (`x = 5` → `int`)
- ✅ Local variables from function returns (`result = foo()` → inferred from `foo()` return type)
- ✅ Empty lists from append usage (`numbers = []; numbers.append(10)` → `list[int]`)
- ✅ Variables from arithmetic operations

**What still needs annotations:**
- ❗ Function parameters (required)
- ❗ Function return types (required)
- ❗ Global variables (required)

See `examples/type_inference_demo.py` for a complete demonstration.

### MGen Pipeline

MGen uses a 7-phase pipeline to translate your code:

```
Python Source
    ↓
1. Validation ────→ Check Python subset
    ↓
2. Analysis ──────→ Parse AST, type inference, semantic analysis
    ↓
3. Python Opt ────→ Python-level optimizations
    ↓
4. Mapping ───────→ Map to target language semantics
    ↓
5. Target Opt ────→ Language-specific optimizations
    ↓
6. Generation ────→ Generate target source code
    ↓
7. Build ─────────→ Compile to executable (optional)
    ↓
Target Executable
```

### Project Structure

After running MGen, your project looks like this:

```
your-project/
├── hello.py              # Your Python source
└── build/                # Generated files (gitignore this)
    ├── src/
    │   ├── hello.cpp     # Generated C++ code
    │   └── ...           # Runtime libraries (for C)
    ├── Makefile          # Build file (if -m flag used)
    └── hello             # Compiled executable (if built)
```

### Command Reference

```bash
# Convert only (no compilation)
mgen --target <lang> convert <file.py>

# Build directly
mgen --target <lang> build <file.py>

# Generate Makefile/Cargo.toml/go.mod
mgen --target <lang> build <file.py> -m

# Clean build directory
mgen clean

# List available backends
mgen backends

# Disable colored output
mgen --target <lang> --no-color convert <file.py>

# Verbose output
mgen --target <lang> -v convert <file.py>
```

---

## Language-Specific Guides

### C++ - Best for Performance and Modern Features

**When to use**: High performance, STL ecosystem, modern C++ features

**Example** (`math_ops.py`):

```python
"""Mathematical operations in C++."""

def factorial(n: int) -> int:
    """Calculate factorial."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def sum_list(numbers: list[int]) -> int:
    """Sum all numbers in a list."""
    total: int = 0
    for num in numbers:
        total += num
    return total

def main() -> int:
    """Main function."""
    fact: int = factorial(5)
    nums: list[int] = [1, 2, 3, 4, 5]
    total: int = sum_list(nums)

    print(fact)
    print(total)
    return 0
```

**Convert and run**:
```bash
mgen --target cpp build math_ops.py
./build/math_ops
```

**Output**:
```
120
15
```

**C++ Features**:
- ✅ STL containers (`std::vector`, `std::unordered_map`)
- ✅ Smart pointers (automatic memory management)
- ✅ Lambda functions (for comprehensions)
- ✅ Modern C++17 features

### Rust - Best for Safety and Systems Programming

**When to use**: Memory safety, systems programming, zero-cost abstractions

**Example** (`string_ops.py`):

```python
"""String operations in Rust."""

def count_words(text: str) -> int:
    """Count words in a string."""
    words: list[str] = text.split()
    return len(words)

def to_uppercase(text: str) -> str:
    """Convert string to uppercase."""
    return text.upper()

def main() -> int:
    """Main function."""
    sentence: str = "hello rust from python"
    word_count: int = count_words(sentence)
    upper: str = to_uppercase(sentence)

    print(word_count)
    print(upper)
    return 0
```

**Convert and run**:
```bash
mgen --target rust build string_ops.py
./build/string_ops
```

**Rust Features**:
- ✅ Ownership system (automatic memory safety)
- ✅ Zero-cost abstractions
- ✅ Pattern matching
- ✅ Cargo ecosystem integration

### Go - Best for Concurrency and Cloud Services

**When to use**: Microservices, cloud applications, simple deployment

**Example** (`data_structures.py`):

```python
"""Data structures in Go."""

def create_list() -> list[int]:
    """Create and populate a list."""
    scores: list[int] = []
    scores.append(95)
    scores.append(87)
    scores.append(92)
    return scores

def find_max(scores: list[int]) -> int:
    """Find maximum score."""
    max_score: int = 0
    for score in scores:
        if score > max_score:
            max_score = score
    return max_score

def main() -> int:
    """Main function."""
    scores: list[int] = create_list()
    max_score: int = find_max(scores)
    print(max_score)
    return 0
```

**Convert and run**:
```bash
mgen --target go build data_structures.py
./build/data_structures
```

**Go Features**:
- ✅ Fast compilation
- ✅ Simple deployment (single binary)
- ✅ Built-in concurrency (goroutines)
- ✅ Garbage collection

### Haskell - Best for Functional Programming

**When to use**: Pure functional code, type safety, mathematical algorithms

**Example** (`functional.py`):

```python
"""Functional programming in Haskell."""

def map_double(numbers: list[int]) -> list[int]:
    """Double each number."""
    return [x * 2 for x in numbers]

def filter_even(numbers: list[int]) -> list[int]:
    """Filter even numbers."""
    result: list[int] = []
    for x in numbers:
        if x % 2 == 0:
            result.append(x)
    return result

def main() -> int:
    """Main function."""
    nums: list[int] = [1, 2, 3, 4, 5, 6]
    doubled: list[int] = map_double(nums)
    evens: list[int] = filter_even(doubled)

    print(doubled)
    print(evens)
    return 0
```

**Convert and run**:
```bash
mgen --target haskell build functional.py
./build/functional
```

**Haskell Features**:
- ✅ Pure functional paradigm
- ✅ Lazy evaluation
- ✅ Strong type system
- ✅ Pattern matching

### OCaml - Best for Type-Safe Functional Code

**When to use**: Functional programming with mutation, theorem proving, compilers

**Example** (`ocaml_demo.py`):

```python
"""OCaml demonstration."""

def accumulate(numbers: list[int]) -> int:
    """Sum all numbers."""
    total: int = 0
    for num in numbers:
        total += num
    return total

def main() -> int:
    """Main function."""
    nums: list[int] = [10, 20, 30, 40, 50]
    total: int = accumulate(nums)
    print(total)
    return 0
```

**Convert and run**:
```bash
mgen --target ocaml build ocaml_demo.py
./build/ocaml_demo
```

**OCaml Features**:
- ✅ Functional + imperative
- ✅ Strong static typing
- ✅ Pattern matching
- ✅ Fast compilation

### C - Best for Embedded and Low-Level

**When to use**: Embedded systems, OS development, maximum control

**Example** (`low_level.py`):

```python
"""Low-level operations in C."""

def array_sum(numbers: list[int]) -> int:
    """Sum array elements."""
    total: int = 0
    for i in range(len(numbers)):
        total += numbers[i]
    return total

def main() -> int:
    """Main function."""
    data: list[int] = [1, 2, 3, 4, 5]
    result: int = array_sum(data)
    print(result)
    return 0
```

**Convert and run**:
```bash
mgen --target c build low_level.py
./build/low_level
```

**C Features**:
- ✅ Maximum performance
- ✅ Full control
- ✅ STC container library (zero external deps)
- ✅ Embedded systems compatible

---

## Common Patterns

### Pattern 1: Lists and Iteration

```python
def process_list(items: list[int]) -> list[int]:
    """Process a list of integers."""
    result: list[int] = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result

def main() -> int:
    numbers: list[int] = [1, -2, 3, -4, 5]
    processed: list[int] = process_list(numbers)
    print(processed)
    return 0
```

**Supported in**: All backends ✅

### Pattern 2: Dictionaries (Hash Maps)

```python
def count_frequency(words: list[str]) -> dict[str, int]:
    """Count word frequencies."""
    freq: dict[str, int] = {}
    for word in words:
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1
    return freq

def main() -> int:
    words: list[str] = ["apple", "banana", "apple", "cherry", "banana", "apple"]
    freq: dict[str, int] = count_frequency(words)
    print(freq)
    return 0
```

**Supported in**: All backends ✅

### Pattern 3: List Comprehensions

```python
def squares(n: int) -> list[int]:
    """Generate list of squares."""
    return [i * i for i in range(n)]

def main() -> int:
    result: list[int] = squares(10)
    print(result)
    return 0
```

**Supported in**: All backends ✅

### Pattern 4: Classes and OOP

```python
class Point:
    """2D Point class."""

    def __init__(self, x: int, y: int):
        """Initialize point."""
        self.x: int = x
        self.y: int = y

    def distance_from_origin(self) -> float:
        """Calculate distance from origin."""
        return (self.x * self.x + self.y * self.y) ** 0.5

def main() -> int:
    p: Point = Point(3, 4)
    dist: float = p.distance_from_origin()
    print(dist)
    return 0
```

**Supported in**: C, C++, Rust, Go ✅

### Pattern 5: File I/O

```python
def read_numbers(filename: str) -> list[int]:
    """Read integers from file."""
    numbers: list[int] = []
    f = open(filename, "r")
    try:
        for line in f:
            numbers.append(int(line.strip()))
    finally:
        f.close()
    return numbers

def main() -> int:
    # Note: Create data.txt with numbers first
    nums: list[int] = read_numbers("data.txt")
    count: int = len(nums)
    print(count)
    return 0
```

**Supported in**: C, C++, Rust, Go ✅

---

## Troubleshooting

### Common Errors and Solutions

#### Tip: Keep print() Statements Simple

For best cross-backend compatibility, use simple `print()` statements:

```python
# ✅ Best - Simple values
print(42)
print("Hello")
print(my_variable)

# ✅ Good - String concatenation with strings only
message = "Hello, " + name + "!"
print(message)

# ⚠️ Avoid - Mixing types in concatenation may have issues
# print("Value: " + str(x))  # str() handling varies by backend

# ✅ Better - Use multiple print statements or variables
print("Value:")
print(x)
```

#### Error: "F-strings (JoinedStr) are not supported"

```python
# ❌ NOT supported
print(f"Result: {value}")

# ✅ Use string concatenation (strings only)
print("Result: " + str_value)

# ✅ Or print values separately
print("Result:")
print(value)
```

#### Error: "Generator expressions are not supported"

```python
# ❌ NOT supported
result = (x * 2 for x in items)

# ✅ Use list comprehension instead
result = [x * 2 for x in items]
```

#### Error: "Async functions are not supported"

```python
# ❌ NOT supported
async def fetch_data():
    await some_operation()

# ✅ Use synchronous functions
def fetch_data():
    some_operation()
```

#### Error: "Lambda expressions are not fully supported"

```python
# ❌ Limited support
callback = lambda x: x * 2

# ✅ Use named function
def callback(x: int) -> int:
    return x * 2
```

#### Error: "Missing type annotation"

```python
# ❌ Missing types
def process(data):
    return data * 2

# ✅ Add type annotations
def process(data: int) -> int:
    return data * 2
```

#### Error: "Context managers (with statement) not supported"

```python
# ❌ NOT supported
with open('file.txt') as f:
    data = f.read()

# ✅ Use try/finally
f = open('file.txt')
try:
    data = f.read()
finally:
    f.close()
```

### Getting Help

1. **Check error messages** - MGen provides helpful suggestions
2. **See [Error Handling Guide](ERROR_HANDLING.md)** - Complete error reference
3. **View examples** - Check `tests/examples/` for working code
4. **Report issues** - https://github.com/yourusername/mgen/issues

---

## Next Steps

### Learn More

- **[Supported Features](SUPPORTED_FEATURES.md)** - Complete Python feature list
- **[Backend Comparison](BACKEND_COMPARISON.md)** - Choose the right backend
- **[Error Handling](ERROR_HANDLING.md)** - Understanding error messages
- **[Examples](../tests/examples/)** - Real-world code examples

### Example Projects

Explore these examples in `tests/examples/`:

1. **CLI Tools** (`cli_tools/wordcount.py`) - Word counter application
2. **Data Processing** (`data_processing/`) - CSV statistics, pipelines
3. **Algorithms** (`algorithms/merge_sort.py`) - Sorting algorithms
4. **Games** (`games/number_guess.py`) - Number guessing game
5. **OOP Demo** (`oop_demo.py`) - Object-oriented programming

### Benchmarks

See `tests/benchmarks/` for performance examples:
- `algorithms/fibonacci.py` - Recursive algorithms
- `algorithms/quicksort.py` - In-place sorting
- `algorithms/matmul.py` - Matrix multiplication
- `algorithms/wordcount.py` - Text processing
- `data_structures/list_ops.py` - List operations
- `data_structures/dict_ops.py` - Dictionary operations
- `data_structures/set_ops.py` - Set operations

### Advanced Topics

Once comfortable with basics, explore:

- **Optimization levels** - `--optimization` flag (none, basic, moderate, aggressive)
- **Backend preferences** - `--prefer` flag for fine-tuning
- **Build customization** - Custom compiler flags and options
- **Module imports** - Multi-file projects
- **Performance tuning** - Language-specific optimizations

---

## Quick Reference

### Installation
```bash
pip install -e .
```

### Basic Commands
```bash
# Convert to C++
mgen --target cpp convert program.py

# Build and run
mgen --target rust build program.py
./build/program

# Generate Makefile
mgen --target cpp build program.py -m

# List backends
mgen backends

# Clean build
mgen clean
```

### Supported Backends
- `c` - C language (gcc/clang)
- `cpp` - C++ (g++/clang++)
- `rust` - Rust (rustc/cargo)
- `go` - Go language (go compiler)
- `haskell` - Haskell (ghc)
- `ocaml` - OCaml (ocamlc)

### Python Requirements
- Python 3.9+ required
- Type annotations mandatory
- `main()` function recommended
- Use supported Python subset

---

**Ready to build something?** Start with the simple examples above, then explore the examples directory for more complex projects!

**Questions?** Check the [FAQ](FAQ.md) or [open an issue](https://github.com/yourusername/mgen/issues).

---

**Last Updated**: 2025-10-05
**Version**: v0.1.59+
**License**: See [LICENSE](../LICENSE)
