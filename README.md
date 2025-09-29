# MGen: Multi-Language Code Generator

MGen translates Python code to multiple target languages while preserving semantics and performance.

## Features

- **Multi-Language Support**: Generate code for C, C++, Rust, Go, Haskell with comprehensive language features

- **Universal Preference System**: Customize code generation for each backend with language-specific preferences

- **Advanced Python Support**: Object-oriented programming, comprehensions, string methods, augmented assignment

- **Modern Libraries**: C++ STL containers, Rust collections, Go standard library integration, Haskell standard library

- **Clean Architecture**: Extensible backend system for adding new languages with preference support

- **Type-Safe Generation**: Leverages Python type annotations for accurate translation

- **CLI Interface**: Simple command-line tool with preference customization for conversion and building

- **Comprehensive Testing**: Full test suite with 684 passing tests (100% success rate) ensuring translation accuracy

## Supported Languages

| Language | Status      | File Extension | Build System      | Advanced Features | Preferences |
|----------|-------------|----------------|-------------------|-------------------|-------------|
| C        | **Enhanced** | `.c`          | Makefile / gcc    | OOP, STC containers, string methods, comprehensions | 12 settings (containers, memory, style) |
| C++      | **Enhanced** | `.cpp`        | Makefile / g++    | OOP, STL containers, string methods, comprehensions | 15 settings (C++ standard, modern features, STL) |
| Rust     | **Enhanced** | `.rs`         | Cargo / rustc     | OOP, std library, string methods, comprehensions, memory safety | 19 settings (edition, ownership, idioms) |
| Go       | **Enhanced** | `.go`         | go.mod / go build | OOP, standard library, string methods, comprehensions | 18 settings (version, concurrency, Go patterns) |
| Haskell  | **Enhanced** | `.hs`         | Cabal / ghc       | OOP, pure functions, string methods, comprehensions, type safety | 12 settings (comprehensions, type system, style) |
| OCaml    | **Enhanced** | `.ml`         | dune / ocamlc     | OOP, functional programming, pattern matching, comprehensions, type safety | 17 settings (version, functional style, modules) |

## Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/shakfu/mgen
cd mgen
pip install -e .
```

### Basic Usage

```bash
# List available backends
mgen backends

# Convert Python to C (with advanced features)
mgen --target c convert my_script.py

# Convert Python to C++ (with STL support)
mgen --target cpp convert my_script.py

# Convert Python to Rust with build
mgen --target rust build my_script.py

# Convert Python to Go (with enhanced features)
mgen --target go convert my_script.py

# Convert Python to Haskell (with functional programming features)
mgen --target haskell convert my_script.py

# Convert Python to OCaml (with functional programming and pattern matching)
mgen --target ocaml convert my_script.py

# Batch convert all Python files
mgen --target cpp batch --source-dir ./examples
```

### Backend Preferences

Customize code generation for each target language with the `--prefer` flag:

```bash
# Haskell with native comprehensions (idiomatic)
mgen --target haskell convert my_script.py --prefer use_native_comprehensions=true

# C with custom settings
mgen --target c convert my_script.py --prefer use_stc_containers=false --prefer indent_size=2

# C++ with modern features
mgen --target cpp convert my_script.py --prefer cpp_standard=c++20 --prefer use_modern_cpp=true

# Rust with specific edition
mgen --target rust convert my_script.py --prefer rust_edition=2018 --prefer clone_strategy=explicit

# Go with version targeting
mgen --target go convert my_script.py --prefer go_version=1.19 --prefer use_generics=false

# OCaml with functional programming preferences
mgen --target ocaml convert my_script.py --prefer prefer_immutable=true --prefer use_pattern_matching=true

# Multiple preferences
mgen --target haskell build my_script.py \
  --prefer use_native_comprehensions=true \
  --prefer camel_case_conversion=false \
  --prefer strict_data_types=true
```

## Preference System

MGen features a comprehensive preference system that allows you to choose between **cross-language consistency** (default) and **language-specific idiomatic optimizations**.

### Design Philosophy

- **Default (Consistent)**: Uses runtime library functions for predictable behavior across all languages
- **Idiomatic (Optimized)**: Uses native language features for better performance and familiarity

### Available Preference Categories

| Backend | Key Preferences | Description |
|---------|-----------------|-------------|
| **Haskell** | `use_native_comprehensions`, `camel_case_conversion`, `strict_data_types` | Native vs runtime comprehensions, naming, type system |
| **C** | `use_stc_containers`, `brace_style`, `indent_size` | Container choice, code style, memory management |
| **C++** | `cpp_standard`, `use_modern_cpp`, `use_stl_containers` | Language standard, modern features, STL usage |
| **Rust** | `rust_edition`, `clone_strategy`, `use_iterators` | Edition targeting, ownership patterns, functional style |
| **Go** | `go_version`, `use_generics`, `naming_convention` | Version compatibility, language features, Go idioms |
| **OCaml** | `prefer_immutable`, `use_pattern_matching`, `curried_functions` | Functional style, pattern matching, function curry style |

### Example: Haskell Comprehensions

**Python Source:**

```python
def filter_numbers(numbers):
    return [x * 2 for x in numbers if x > 5]
```

**Default (Runtime Consistency):**

```haskell
filterNumbers numbers = listComprehensionWithFilter numbers (\x -> x > 5) (\x -> x * 2)
```

**Native (Idiomatic Haskell):**

```haskell
filterNumbers numbers = [x * 2 | x <- numbers, x > 5]
```

### Example: OCaml Functional Programming

**Python Source:**

```python
def process_items(items):
    return [item.upper() for item in items if len(item) > 3]
```

**Default (Runtime Consistency):**

```ocaml
let process_items items =
  list_comprehension_with_filter items (fun item -> len item > 3) (fun item -> upper item)
```

**Functional (Idiomatic OCaml):**

```ocaml
let process_items items =
  List.filter (fun item -> String.length item > 3) items
  |> List.map String.uppercase_ascii
```

For complete preference documentation, see [PREFERENCES.md](PREFERENCES.md).

## Examples

### Simple Functions

**Python Input:**

```python
def add(x: int, y: int) -> int:
    return x + y

def main() -> None:
    result = add(5, 3)
    print(result)
```

**Generated C++:**

```cpp
#include <iostream>
#include <vector>
#include <unordered_map>
#include "runtime/mgen_cpp_runtime.hpp"

using namespace std;
using namespace mgen;

int add(int x, int y) {
    return (x + y);
}

void main() {
    int result = add(5, 3);
    cout << result << endl;
}
```

**Generated C:**

```c
#include <stdio.h>
#include "mgen_runtime.h"

int add(int x, int y) {
    return (x + y);
}

void main() {
    int result = add(5, 3);
    printf("%d\n", result);
}
```

**Generated Go:**

```go
package main

import "mgen"

func add(x int, y int) int {
    return (x + y)
}

func main() {
    result := add(5, 3)
    mgen.Print(result)
}
```

**Generated Rust:**

```rust
// Include MGen Rust runtime
mod mgen_rust_runtime;
use mgen_rust_runtime::*;

fn add(x: i32, y: i32) -> i32 {
    (x + y)
}

fn main() {
    let mut result = add(5, 3);
    print_value(result);
}
```

**Generated Haskell:**

```haskell
module Main where

import MGenRuntime
import qualified Data.Map as Map
import qualified Data.Set as Set
import Data.Map (Map)
import Data.Set (Set)

add :: Int -> Int -> Int
add x y = (x + y)

main :: IO ()
main = printValue (add 5 3)
```

**Generated OCaml:**

```ocaml
(* Generated OCaml code from Python *)

open Mgen_runtime

let add x y =
  (x + y)

let main () =
  let result = add 5 3 in
  print_value result

let () = print_value "Generated OCaml code executed successfully"
```

### Advanced Features (Object-Oriented Programming)

**Python Input:**

```python
class Calculator:
    def __init__(self, name: str):
        self.name: str = name
        self.total: int = 0

    def add(self, value: int) -> None:
        self.total += value

    def get_result(self) -> str:
        return self.name.upper() + ": " + str(self.total)

def process() -> list:
    calc = Calculator("math")
    calc.add(10)
    return [calc.get_result() for _ in range(2)]
```

**Generated C++:**

```cpp
#include <iostream>
#include <string>
#include <vector>
#include "runtime/mgen_cpp_runtime.hpp"

using namespace std;
using namespace mgen;

class Calculator {
public:
    std::string name;
    int total;

    Calculator(std::string name) {
        this->name = name;
        this->total = 0;
    }

    void add(int value) {
        this->total += value;
    }

    std::string get_result() {
        return (StringOps::upper(this->name) + (": " + to_string(this->total)));
    }
};

std::vector<std::string> process() {
    Calculator calc("math");
    calc.add(10);
    return list_comprehension(Range(2), [&](auto _) {
        return calc.get_result();
    });
}
```

**Generated Go:**

```go
package main

import "mgen"

type Calculator struct {
    Name string
    Total int
}

func NewCalculator(name string) Calculator {
    obj := Calculator{}
    obj.Name = name
    obj.Total = 0
    return obj
}

func (obj *Calculator) Add(value int) {
    obj.Total += value
}

func (obj *Calculator) GetResult() string {
    return (mgen.StrOps.Upper(obj.Name) + (": " + mgen.ToStr(obj.Total)))
}

func process() []interface{} {
    calc := NewCalculator("math")
    calc.Add(10)
    return mgen.Comprehensions.ListComprehension(mgen.NewRange(2), func(item interface{}) interface{} {
        _ := item.(int)
        return calc.GetResult()
    })
}
```

**Generated Rust:**

```rust
use std::collections::{HashMap, HashSet};

// Include MGen Rust runtime
mod mgen_rust_runtime;
use mgen_rust_runtime::*;

#[derive(Clone)]
struct Calculator {
    name: String,
    total: i32,
}

impl Calculator {
    fn new(name: String) -> Self {
        Calculator {
            name: name,
            total: 0,
        }
    }

    fn add(&mut self, value: i32) {
        self.total += value;
    }

    fn get_result(&mut self) -> String {
        ((StrOps::upper(&self.name) + ": ".to_string()) + to_string(self.total))
    }
}

fn process() -> Vec<String> {
    let mut calc = Calculator::new("math".to_string());
    calc.add(10);
    Comprehensions::list_comprehension(new_range(2).collect(), |_| calc.get_result())
}
```

**Generated Haskell:**

```haskell
{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE FlexibleInstances #-}

module Main where

import MGenRuntime
import qualified Data.Map as Map
import qualified Data.Set as Set
import Data.Map (Map)
import Data.Set (Set)

data Calculator = Calculator
  { name :: String
  , total :: Int
  } deriving (Show, Eq)

newCalculator :: String -> Calculator
newCalculator name = Calculator { name = name, total = 0 }

add :: Calculator -> Int -> ()
add obj value = ()  -- Haskell immutable approach

getResult :: Calculator -> String
getResult obj = (upper (name obj)) + ": " + (toString (total obj))

process :: [String]
process =
  let calc = newCalculator "math"
  in listComprehension (rangeList (range 2)) (\_ -> getResult calc)
```

**Generated OCaml:**

```ocaml
(* Generated OCaml code from Python *)

open Mgen_runtime

type calculator = {
  name : string;
  total : int;
}

let create_calculator name =
  {
    name = name;
    total = 0;
  }

let calculator_add (calculator_obj : calculator) value =
  (* Functional update creating new record *)
  { calculator_obj with total = calculator_obj.total + value }

let calculator_get_result (calculator_obj : calculator) =
  (calculator_obj.name ^ ": " ^ string_of_int calculator_obj.total)

let process () =
  let calc = create_calculator "math" in
  let updated_calc = calculator_add calc 10 in
  list_comprehension (range_list (range 2)) (fun _ -> calculator_get_result updated_calc)
```

## Architecture

MGen follows a clean, extensible architecture with three main components:

### Frontend (Language-Agnostic)

- **Type Inference**: Analyzes Python type annotations
- **Static Analysis**: Validates code compatibility
- **AST Processing**: Parses and transforms Python syntax

### Backends (Language-Specific)

- **Abstract Interfaces**: Common API for all target languages
- **Code Generation**: Language-specific syntax and idioms
- **Build Systems**: Native toolchain integration

### Pipeline

- **Multi-Phase Processing**: Validation → Analysis → Generation → Build
- **Error Handling**: Comprehensive error reporting and recovery
- **Optimization**: Language-specific performance optimizations

## CLI Commands

### Convert

Convert Python files to target language:

```bash
mgen --target <language> convert <input.py>
mgen --target rust convert example.py
```

### Build

Convert and compile/build the result:

```bash
mgen --target <language> build <input.py>
mgen --target go build --makefile example.py  # Generate build file
mgen --target c build example.py              # Direct compilation
```

### Batch

Process multiple files:

```bash
mgen --target <language> batch --source-dir <dir>
mgen --target rust batch --source-dir ./src --build
```

### Backends

List available language backends:

```bash
mgen backends
```

### Clean

Clean build artifacts:

```bash
mgen clean
```

## Development

### Running Tests

```bash
make test           # Run all tests
make test-unit      # Run unit tests only
make lint           # Run code linting
make type-check     # Run type checking
```

### Adding New Backends

1. Create backend directory: `src/mgen/backends/mylang/`
2. Implement required classes:
   - `MyLangBackend(LanguageBackend)`
   - `MyLangFactory(AbstractFactory)`
   - `MyLangEmitter(AbstractEmitter)`
   - `MyLangBuilder(AbstractBuilder)`
   - `MyLangContainerSystem(AbstractContainerSystem)`
3. Register in `registry.py`
4. Add tests

See existing backends for examples.

## Comparison with CGen

MGen is inspired by and builds upon concepts from the [CGen](https://github.com/shakfu/cgen) project.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Advanced Features

### C/C++/Go Backends

The C, C++, and Go backends support sophisticated Python language features:

- **Object-Oriented Programming**: Classes, methods, constructors, inheritance
- **Advanced Assignment**: Augmented operators (`+=`, `-=`, `*=`, etc.)
- **String Operations**: `upper()`, `lower()`, `strip()`, `find()`, `replace()`, `split()`
- **Comprehensions**: List, dict, and set comprehensions with conditional filtering
- **Type Inference**: Automatic type detection and smart C/C++ type mapping
- **Container Support**:
  - C: STC (Smart Template Container) high-performance containers
  - C++: STL containers (`std::vector`, `std::unordered_map`, `std::unordered_set`)
  - Go: Standard library containers with functional programming patterns
  - Haskell: Standard library containers with type-safe functional operations

### Test Coverage

- **684 passing tests** across all backends (100% success rate)
- **104 C++ backend tests** (104 passing, 100% success rate)
- **191 C backend tests** with comprehensive advanced features
- **95 Go backend tests** (95 passing, 100% success rate)
- **176 Rust backend tests** with comprehensive OOP, string methods, and comprehensions support
- **93 Haskell backend tests** with functional programming patterns and type safety (100% success rate)
- **25 OCaml backend tests** with functional programming, pattern matching, and type safety (100% success rate)
- Specialized test suites for OOP, string methods, comprehensions, and more

## Roadmap

- [x] **C++ Backend Enhancement** - STL-based runtime with feature parity to C backend
- [x] **Advanced Python Features** - OOP, comprehensions, string methods, augmented assignment
- [x] **Comprehensive Testing** - 659 tests with 100% success rate ensuring translation accuracy
- [x] **Production-Ready C++ Backend** - Complete feature parity with advanced comprehension support
- [x] **Go Backend Enhancement** - Complete feature parity with C/C++ backends using Go standard library
- [x] **Rust Backend Enhancement** - Complete feature parity with C/C++/Go backends using Rust standard library
- [x] **Haskell Backend Enhancement** - Complete functional programming backend with type safety and Haskell standard library
- [x] **OCaml Backend Enhancement** - Complete functional programming backend with pattern matching, immutable data structures, and OCaml standard library
- [x] **Universal Preference System** - Language-specific customization for all backends with CLI integration
- [ ] **Performance Benchmarking** - Cross-language performance analysis
- [ ] **Web Interface** - Online code conversion tool
- [ ] **Plugin System** - External backend support
