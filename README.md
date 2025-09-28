# MGen: Multi-Language Code Generator

MGen translates Python code to multiple target languages while preserving semantics and performance.

## Features

- **Multi-Language Support**: Generate code for C, Rust, Go, and more
- **Clean Architecture**: Extensible backend system for adding new languages
- **Type-Safe Generation**: Leverages Python type annotations for accurate translation
- **CLI Interface**: Simple command-line tool for conversion and building
- **Comprehensive Testing**: Full test suite ensuring translation accuracy

## Supported Languages

| Language | Status  | File Extension | Build System  		|
|----------|---------|----------------|---------------------|
| C        | Started | `.c` 		  | Makefile / gcc 		|
| Rust     | Started | `.rs` 		  | Cargo / rustc 		|
| Go       | Started | `.go` 		  | go.mod / go build 	|
| C++      | Planned | `.cpp` 		  | CMake / g++ 		|

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

# Convert Python to C
mgen --target c convert my_script.py

# Convert Python to Rust with build
mgen --target rust build my_script.py

# Convert Python to Go
mgen --target go convert my_script.py

# Batch convert all Python files
mgen --target c batch --source-dir ./examples
```

## Examples

### Python Input
```python
def add(x: int, y: int) -> int:
    return x + y

def main():
    result = add(5, 3)
    print(f"5 + 3 = {result}")
```

### Generated C
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

int add(int x, int y) {
    return x + y;
}

int main() {
    printf("Hello from MGen-generated C code!\n");
    return 0;
}
```

### Generated Rust
```rust
fn add(x: i32, y: i32) -> i32 {
    x + y
}

fn main() {
    println!("Hello from MGen-generated Rust code!");
}
```

### Generated Go
```go
package main

import "fmt"

func add(x int, y int) int {
    return x + y
}

func main() {
    fmt.Println("Hello from MGen-generated Go code!")
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

## Roadmap

- [ ] C++ backend implementation
- [ ] Advanced type inference
- [ ] Container operations support
- [ ] Cross-language interop
- [ ] Performance benchmarking
- [ ] Web interface
- [ ] Plugin system for external backends
