# MGen Use Cases & Integration Patterns

This guide provides real-world use cases and integration patterns for MGen across different scenarios.

---

## Table of Contents

1. [Embedding Python Logic in C Applications](#1-embedding-python-logic-in-c-applications)
2. [Building Fast Native Python Extensions](#2-building-fast-native-python-extensions)
3. [WebAssembly Modules for Web Applications](#3-webassembly-modules-for-web-applications)
4. [Cloud Microservices from Python Prototypes](#4-cloud-microservices-from-python-prototypes)
5. [Command-Line Tools with Fast Startup](#5-command-line-tools-with-fast-startup)
6. [Embedded Systems & IoT Devices](#6-embedded-systems--iot-devices)
7. [High-Performance Data Processing Pipelines](#7-high-performance-data-processing-pipelines)
8. [Game Logic & Plugin Systems](#8-game-logic--plugin-systems)
9. [Configuration DSLs & Parsers](#9-configuration-dsls--parsers)
10. [Mathematical & Scientific Computing](#10-mathematical--scientific-computing)

---

## 1. Embedding Python Logic in C Applications

### Use Case

You have complex business logic written in Python that needs to run in a C/C++ application (legacy systems, drivers, embedded firmware).

### Recommended Backend

**C** - Direct FFI, zero overhead, universal compatibility

### Example Workflow

```python
# algorithm.py
def calculate_score(points: int, multiplier: int) -> int:
    """Calculate game score"""
    return points * multiplier + 100

def main() -> int:
    result: int = calculate_score(10, 5)
    print(result)
    return 0
```

**Generate C code:**
```bash
mgen --target c convert algorithm.py
```

**Integrate in existing C application:**
```c
// main_app.c
#include "build/src/algorithm.h"

int main() {
    // Call MGen-generated function
    int score = calculate_score(10, 5);
    printf("Score: %d\n", score);
    return 0;
}
```

**Compile together:**
```bash
gcc main_app.c build/src/algorithm.c -o app
```

### Benefits

- No Python runtime required
- Direct function calls (no marshalling overhead)
- Small binary size (66KB avg)
- Predictable performance

---

## 2. Building Fast Native Python Extensions

### Use Case

Performance-critical Python code needs to run 10-100x faster. Convert to Rust/C++ and load as Python extension.

### Recommended Backend

**Rust** (via PyO3) or **C++** (via pybind11)

### Example Workflow

**Rust approach:**

```python
# matrix_ops.py - expensive computation
def matmul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    """Matrix multiplication"""
    n: int = len(a)
    m: int = len(b[0])
    k: int = len(b)

    result: list[list[int]] = [[0 for _ in range(m)] for _ in range(n)]

    for i in range(n):
        for j in range(m):
            sum_val: int = 0
            for p in range(k):
                sum_val += a[i][p] * b[p][j]
            result[i][j] = sum_val

    return result
```

**Convert to Rust:**
```bash
mgen --target rust convert matrix_ops.py
```

**Wrap with PyO3:**
```rust
// src/lib.rs
use pyo3::prelude::*;

// Include MGen-generated code
include!("../build/src/matrix_ops.rs");

#[pyfunction]
fn fast_matmul(a: Vec<Vec<i32>>, b: Vec<Vec<i32>>) -> PyResult<Vec<Vec<i32>>> {
    Ok(matmul(&a, &b))
}

#[pymodule]
fn matrix_ops_fast(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_matmul, m)?)?;
    Ok(())
}
```

**Build Python extension:**
```bash
cargo build --release
```

**Use from Python:**
```python
import matrix_ops_fast

result = matrix_ops_fast.fast_matmul(a, b)  # 50x faster!
```

### Benefits

- 10-100x speedup for compute-intensive code
- Memory safety (Rust) or mature ecosystem (C++)
- Seamless Python integration
- Gradual migration path

---

## 3. WebAssembly Modules for Web Applications

### Use Case

Run Python algorithms in the browser for client-side computation, offline processing, or privacy-sensitive data.

### Recommended Backend

**Rust** → WebAssembly

### Example Workflow

```python
# text_processor.py
def word_count(text: str) -> int:
    """Count words in text"""
    words: list[str] = text.split()
    return len(words)

def main() -> int:
    text: str = "Hello world from MGen"
    count: int = word_count(text)
    print(count)
    return 0
```

**Convert to Rust:**
```bash
mgen --target rust convert text_processor.py
```

**Compile to WASM:**
```bash
cd build/src
wasm-pack build --target web
```

**Use in JavaScript:**
```javascript
import init, { word_count } from './pkg/text_processor.js';

await init();
const count = word_count("Hello world from MGen");
console.log(`Word count: ${count}`);
```

### Benefits

- No server round-trips for computation
- Privacy - data never leaves the browser
- Portable across all platforms
- Fast startup (Rust WASM is optimized)

---

## 4. Cloud Microservices from Python Prototypes

### Use Case

Prototype in Python, deploy as high-performance Go microservice with fast builds and low memory footprint.

### Recommended Backend

**Go** - Fast compilation (63ms avg), built-in concurrency, single binary deployment

### Example Workflow

```python
# api_handler.py
def validate_email(email: str) -> bool:
    """Validate email format"""
    return "@" in email and "." in email

def process_request(email: str, count: int) -> int:
    """Process API request"""
    if not validate_email(email):
        return -1
    return count * 2

def main() -> int:
    result: int = process_request("user@example.com", 10)
    print(result)
    return 0
```

**Convert to Go:**
```bash
mgen --target go build api_handler.py
```

**Wrap in HTTP server:**
```go
// server.go
package main

import (
    "encoding/json"
    "net/http"
    "log"

    // Import MGen-generated code
    "./build/src"
)

type Request struct {
    Email string `json:"email"`
    Count int    `json:"count"`
}

func handler(w http.ResponseWriter, r *http.Request) {
    var req Request
    json.NewDecoder(r.Body).Decode(&req)

    result := src.ProcessRequest(req.Email, req.Count)

    json.NewEncoder(w).Encode(map[string]int{"result": result})
}

func main() {
    http.HandleFunc("/process", handler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

**Deploy:**
```bash
go build -o server server.go
./server  # Single binary, fast startup, low memory
```

### Benefits

- Fast iteration during development (Python prototype)
- Fast builds for deployment (Go: 63ms compile)
- Low memory footprint (efficient GC)
- Built-in concurrency (goroutines)
- Single static binary deployment

---

## 5. Command-Line Tools with Fast Startup

### Use Case

Build CLI utilities that start instantly and distribute as single binaries.

### Recommended Backend

**Go** (fastest startup) or **C++** (smallest binary)

### Example Workflow

```python
# file_analyzer.py
def count_lines(filename: str) -> int:
    """Count lines in a file"""
    count: int = 0
    with open(filename, 'r') as f:
        for line in f:
            count += 1
    return count

def main() -> int:
    # Parse args and process files
    count: int = count_lines("README.md")
    print(count)
    return 0
```

**Convert to Go:**
```bash
mgen --target go build file_analyzer.py
```

**Add CLI interface:**
```go
package main

import (
    "flag"
    "fmt"
    "os"

    "./build/src"
)

func main() {
    filename := flag.String("file", "", "File to analyze")
    flag.Parse()

    if *filename == "" {
        fmt.Println("Usage: analyzer --file <filename>")
        os.Exit(1)
    }

    count := src.CountLines(*filename)
    fmt.Printf("Lines: %d\n", count)
}
```

**Build and distribute:**
```bash
go build -ldflags="-s -w" -o analyzer
# Distribute single binary
```

### Benefits

- Instant startup (no Python interpreter overhead)
- Single binary distribution
- Cross-platform compilation
- Fast execution

---

## 6. Embedded Systems & IoT Devices

### Use Case

Deploy Python logic to resource-constrained devices (microcontrollers, sensors, edge devices).

### Recommended Backend

**C++** (smallest binaries: 34KB) or **C** (universal compatibility)

### Example Workflow

```python
# sensor_logic.py
def process_reading(temp: int, humidity: int) -> int:
    """Process sensor data"""
    if temp > 30 and humidity > 70:
        return 2  # Alert level
    elif temp > 25:
        return 1  # Warning level
    return 0  # Normal

def main() -> int:
    level: int = process_reading(28, 65)
    print(level)
    return 0
```

**Convert to C++:**
```bash
mgen --target cpp build sensor_logic.py
```

**Integrate with embedded SDK:**
```cpp
// device_main.cpp
#include "build/src/sensor_logic.hpp"
#include "sensor_hardware.h"  // Device-specific SDK

void loop() {
    int temp = read_temperature();
    int humidity = read_humidity();

    int alert_level = process_reading(temp, humidity);

    if (alert_level > 0) {
        trigger_alert(alert_level);
    }

    delay(1000);
}
```

**Cross-compile for device:**
```bash
arm-none-eabi-g++ -Os -o firmware.elf device_main.cpp build/src/sensor_logic.cpp
```

### Benefits

- Tiny binaries (34KB for C++, fits in 64KB flash)
- No runtime dependencies
- Low power consumption
- Predictable timing
- Cross-compilation support

---

## 7. High-Performance Data Processing Pipelines

### Use Case

Transform, filter, and aggregate large datasets with functional programming patterns.

### Recommended Backend

**Haskell** (pure transformations) or **OCaml** (performance + functional)

### Example Workflow

```python
# data_pipeline.py
def filter_valid(numbers: list[int]) -> list[int]:
    """Filter valid numbers"""
    return [x for x in numbers if x > 0]

def transform(numbers: list[int]) -> list[int]:
    """Transform data"""
    return [x * 2 for x in numbers]

def aggregate(numbers: list[int]) -> int:
    """Aggregate results"""
    total: int = 0
    for x in numbers:
        total += x
    return total

def main() -> int:
    data: list[int] = [1, -2, 3, 4, -5]
    valid: list[int] = filter_valid(data)
    transformed: list[int] = transform(valid)
    result: int = aggregate(transformed)
    print(result)
    return 0
```

**Convert to Haskell:**
```bash
mgen --target haskell build data_pipeline.py
```

**Compose into larger pipeline:**
```haskell
-- pipeline.hs
import qualified DataPipeline as DP

processFiles :: [FilePath] -> IO Int
processFiles files = do
    results <- mapM processFile files
    return $ DP.aggregate results

processFile :: FilePath -> IO Int
processFile path = do
    content <- readFile path
    let numbers = map read (lines content) :: [Int]
    let valid = DP.filterValid numbers
    let transformed = DP.transform valid
    return $ DP.aggregate transformed

main :: IO ()
main = do
    result <- processFiles ["data1.txt", "data2.txt"]
    print result
```

### Benefits

- Pure functional transformations
- Lazy evaluation for large datasets
- Type safety prevents errors
- Composable pipeline stages
- Parallel processing potential

---

## 8. Game Logic & Plugin Systems

### Use Case

Hot-reload game logic without restarting the entire game engine, or create modding systems.

### Recommended Backend

**C++** (engine integration) or **Rust** (memory safety)

### Example Workflow

```python
# npc_behavior.py
def calculate_damage(attack: int, defense: int) -> int:
    """Calculate damage dealt"""
    damage: int = attack - defense
    return max(damage, 1)

def should_flee(health: int, enemy_health: int) -> bool:
    """Decide if NPC should flee"""
    return health < enemy_health // 2

def main() -> int:
    dmg: int = calculate_damage(50, 20)
    print(dmg)
    return 0
```

**Convert to C++:**
```bash
mgen --target cpp convert npc_behavior.py
```

**Load as plugin in game engine:**
```cpp
// game_engine.cpp
#include "build/src/npc_behavior.hpp"
#include "npc_system.h"

class NPCController {
private:
    // Hot-reload plugin
    void* plugin_handle;

public:
    void update(NPC& npc, NPC& enemy) {
        int damage = calculate_damage(npc.attack, enemy.defense);
        enemy.health -= damage;

        bool should_flee_now = should_flee(npc.health, enemy.health);
        if (should_flee_now) {
            npc.state = NPCState::FLEEING;
        }
    }

    void reload_plugin() {
        // Rebuild and reload npc_behavior.cpp
        system("make rebuild_plugin");
        // dlopen/dlclose for hot-reload
    }
};
```

### Benefits

- Small plugin binaries (C++: 36KB)
- Hot-reload during development
- Fast execution (139ms avg)
- Modding friendly
- Prototype in Python, deploy optimized

---

## 9. Configuration DSLs & Parsers

### Use Case

Define custom configuration languages or parsers with type safety.

### Recommended Backend

**Haskell** (parser combinators) or **OCaml** (pattern matching)

### Example Workflow

```python
# config_parser.py
def parse_line(line: str) -> dict[str, str]:
    """Parse configuration line"""
    parts: list[str] = line.split("=")
    if len(parts) != 2:
        return {}

    result: dict[str, str] = {}
    result[parts[0].strip()] = parts[1].strip()
    return result

def main() -> int:
    config: dict[str, str] = parse_line("timeout=30")
    print(config.get("timeout", ""))
    return 0
```

**Convert to Haskell:**
```bash
mgen --target haskell convert config_parser.py
```

**Extend with parser combinators:**
```haskell
-- Extended parser
import qualified ConfigParser as CP
import Text.Parsec

type Config = Map String String

parseConfig :: String -> Either String Config
parseConfig input =
    let lines = splitLines input
        pairs = map CP.parseLine lines
    in Right $ Map.fromList $ concat pairs

loadConfig :: FilePath -> IO Config
loadConfig path = do
    content <- readFile path
    case parseConfig content of
        Left err -> error err
        Right cfg -> return cfg
```

### Benefits

- Type safety prevents config errors
- Pure functional parsing
- Easy to extend with combinators
- Compact generated code (27 LOC avg)
- Fast compilation (OCaml: 233ms)

---

## 10. Mathematical & Scientific Computing

### Use Case

Implement numerical algorithms with correctness guarantees and good performance.

### Recommended Backend

**Rust** (safety) or **OCaml** (mathematical elegance)

### Example Workflow

```python
# numerical.py
def gcd(a: int, b: int) -> int:
    """Greatest common divisor"""
    while b != 0:
        temp: int = b
        b = a % b
        a = temp
    return a

def factorial(n: int) -> int:
    """Calculate factorial"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def main() -> int:
    result: int = gcd(48, 18)
    fact: int = factorial(5)
    print(result + fact)
    return 0
```

**Convert to Rust:**
```bash
mgen --target rust build numerical.py
```

**Use in larger scientific code:**
```rust
// scientific.rs
use numerical::{gcd, factorial};

fn lcm(a: i32, b: i32) -> i32 {
    (a * b) / gcd(a, b)
}

fn binomial(n: i32, k: i32) -> i32 {
    factorial(n) / (factorial(k) * factorial(n - k))
}

fn main() {
    println!("LCM(12, 18): {}", lcm(12, 18));
    println!("C(5,2): {}", binomial(5, 2));
}
```

### Benefits

- Memory safety prevents bugs
- Fast execution (153ms avg for Rust)
- No runtime overhead
- Easy integration with existing numerical libraries
- Gradual migration from Python prototypes

---

## Integration Patterns

### Pattern 1: Gradual Migration

Start with critical hot-paths, migrate incrementally:

1. Profile Python code to find bottlenecks
2. Convert hot functions with MGen
3. Integrate via FFI/extensions
4. Measure performance gains
5. Iterate

### Pattern 2: Prototype → Production

Rapid prototyping workflow:

1. Prototype algorithm in Python (fast iteration)
2. Validate with Python tests
3. Convert to production backend (C++/Rust/Go)
4. Deploy optimized version
5. Keep Python as reference implementation

### Pattern 3: Polyglot Systems

Use best tool for each component:

- **UI**: Python (rapid dev) or Go (web services)
- **Performance**: Rust (safety) or C++ (mature)
- **Data processing**: Haskell/OCaml (functional)
- **System integration**: C (universal FFI)

### Pattern 4: Cross-Compilation Workflow

Deploy to multiple platforms:

```bash
# Linux x86_64
mgen --target rust build algorithm.py
cargo build --release

# WebAssembly
cargo build --target wasm32-unknown-unknown

# ARM embedded
cargo build --target arm-unknown-linux-gnueabi
```

---

## Decision Tree by Use Case

```
What's your primary goal?

├─ Embed in C/C++ application → C backend
├─ Speed up Python → Rust + PyO3 or C++ + pybind11
├─ Run in browser → Rust → WebAssembly
├─ Cloud microservice → Go backend
├─ CLI tool (fast startup) → Go backend
├─ CLI tool (small binary) → C++ backend
├─ Embedded/IoT → C++ (size) or C (compatibility)
├─ Data pipeline → Haskell (pure) or OCaml (performance)
├─ Game plugin → C++ (integration) or Rust (safety)
├─ Parser/DSL → Haskell or OCaml (pattern matching)
└─ Scientific computing → Rust (safety) or OCaml (elegance)
```

---

## Best Practices

### 1. Type Everything
```python
# Good - explicit types for clean translation
def process(data: list[int]) -> int:
    count: int = len(data)
    return count

# Bad - missing types, inference may fail
def process(data):
    count = len(data)
    return count
```

### 2. Use Supported Features
Stick to MGen-compatible Python subset (see docs/GETTING_STARTED.md).

### 3. Benchmark Before Optimizing
Profile Python first, convert bottlenecks only.

### 4. Test Both Versions
Keep Python as reference, test generated code matches:
```bash
python algorithm.py > expected.txt
./build/algorithm > actual.txt
diff expected.txt actual.txt
```

### 5. Version Control Generated Code
Consider committing generated code for reproducibility:
```bash
git add build/src/*.c
```

---

## Resources

- **Getting Started**: `docs/GETTING_STARTED.md`
- **Backend Selection**: `docs/BACKEND_SELECTION.md`
- **Error Handling**: `docs/ERROR_HANDLING.md`
- **Examples**: Browse `examples/` directory
- **Issues**: https://github.com/YOUR_ORG/mgen/issues

---

**Version**: 1.0 (October 2025)

**Updated**: Reflects v0.1.61 capabilities
