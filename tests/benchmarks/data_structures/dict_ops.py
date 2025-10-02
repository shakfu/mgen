"""Dictionary operations benchmark - Test dict comprehensions and operations."""


def dict_comprehensions() -> int:
    """Benchmark dictionary comprehensions."""
    # Create dictionary from range
    numbers: dict = {x: x * 2 for x in range(50)}

    # Filter dictionary
    filtered: dict = {k: v for k, v in numbers.items() if v > 20}

    # Sum all values
    total: int = 0
    for value in filtered.values():
        total += value

    return total


def dict_operations() -> int:
    """Benchmark basic dictionary operations."""
    # Create dictionary
    data: dict = {}

    # Insert operations
    for i in range(50):
        data[i] = i * 3

    # Lookup operations
    sum_val: int = 0
    for i in range(50):
        if i in data:
            sum_val += data[i]

    # Length operations
    length: int = len(data)
    sum_val += length

    return sum_val


def main() -> int:
    """Run dictionary operations benchmark."""
    result1: int = 0
    result2: int = 0

    # Run comprehensions benchmark 200 times
    for i in range(200):
        result1 = dict_comprehensions()

    # Run basic operations benchmark 200 times
    for i in range(200):
        result2 = dict_operations()

    # Print combined result
    print(result1 + result2)

    return 0
