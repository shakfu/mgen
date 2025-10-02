"""List operations benchmark - Test list comprehensions and operations."""


def list_comprehensions() -> int:
    """Benchmark list comprehensions."""
    # Create large list
    numbers: list = [x for x in range(100)]

    # Filter even numbers
    evens: list = [x for x in numbers if x % 2 == 0]

    # Square all numbers
    squares: list = [x * x for x in evens]

    # Sum using loop
    total: int = 0
    for num in squares:
        total += num

    return total


def list_operations() -> int:
    """Benchmark basic list operations."""
    # Create list
    data: list = []

    # Append operations
    for i in range(100):
        data.append(i)

    # Access operations
    sum_val: int = 0
    for i in range(100):
        sum_val += data[i]

    # Length operations
    length: int = len(data)
    sum_val += length

    return sum_val


def main() -> int:
    """Run list operations benchmark."""
    result1: int = 0
    result2: int = 0

    # Run comprehensions benchmark 100 times
    for i in range(100):
        result1 = list_comprehensions()

    # Run basic operations benchmark 100 times
    for i in range(100):
        result2 = list_operations()

    # Print combined result
    print(result1 + result2)

    return 0
