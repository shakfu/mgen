# MGen: Multi-Language Code Generator

MGen translates Python code to multiple target languages while preserving semantics and performance.

## Features

- **Multi-Language Support**: Generate code for C, C++, Rust, Go with comprehensive language features
- **Advanced Python Support**: Object-oriented programming, comprehensions, string methods, augmented assignment
- **STL & Modern Libraries**: C++ STL containers, Rust collections, Go standard library integration
- **Clean Architecture**: Extensible backend system for adding new languages
- **Type-Safe Generation**: Leverages Python type annotations for accurate translation
- **CLI Interface**: Simple command-line tool for conversion and building
- **Comprehensive Testing**: Full test suite with 354 passing tests (98% success rate) ensuring translation accuracy

## Supported Languages

| Language | Status      | File Extension | Build System      | Advanced Features |
|----------|-------------|----------------|-------------------|-------------------|
| C        | **Enhanced** | `.c`          | Makefile / gcc    | OOP, STC containers, string methods, comprehensions |
| C++      | **Enhanced** | `.cpp`        | Makefile / g++    | OOP, STL containers, string methods, comprehensions |
| Rust     | Basic       | `.rs`         | Cargo / rustc     | Basic functions, control flow |
| Go       | **Enhanced** | `.go`         | go.mod / go build | OOP, standard library, string methods, comprehensions |

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

# Batch convert all Python files
mgen --target cpp batch --source-dir ./examples
```

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

### Test Coverage

- **354 passing tests** across all backends (98% success rate)
- **104 C++ backend tests** (104 passing, 100% success rate)
- **191 C backend tests** with comprehensive advanced features
- **95 Go backend tests** (95 passing, 100% success rate)
- Specialized test suites for OOP, string methods, comprehensions, and more

## Roadmap

- [x] **C++ Backend Enhancement** - STL-based runtime with feature parity to C backend
- [x] **Advanced Python Features** - OOP, comprehensions, string methods, augmented assignment
- [x] **Comprehensive Testing** - 354 tests with 98% success rate ensuring translation accuracy
- [x] **Production-Ready C++ Backend** - Complete feature parity with advanced comprehension support
- [x] **Go Backend Enhancement** - Complete feature parity with C/C++ backends using Go standard library
- [ ] **Rust Backend Enhancement** - Expand beyond basic functions
- [ ] **Performance Benchmarking** - Cross-language performance analysis
- [ ] **Web Interface** - Online code conversion tool
- [ ] **Plugin System** - External backend support
