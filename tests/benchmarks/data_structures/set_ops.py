"""Set operations benchmark - Test set comprehensions and operations."""


def set_comprehensions() -> int:
    """Benchmark set comprehensions."""
    # Create set from range
    numbers: set = {x for x in range(100)}

    # Filter set
    filtered: set = {x for x in numbers if x % 3 == 0}

    # Count elements
    count: int = len(filtered)

    return count


def set_operations() -> int:
    """Benchmark basic set operations."""
    # Create set
    data: set = set()

    # Add operations (simulated - using dict as workaround)
    temp_dict: dict = {}
    for i in range(100):
        temp_dict[i] = 1  # Use 1 instead of True for LLVM backend compatibility

    # Membership testing
    found_count: int = 0
    for i in range(100):
        if i in temp_dict:
            found_count += 1

    # Length operations
    length: int = len(temp_dict)
    found_count += length

    return found_count


def main() -> int:
    """Run set operations benchmark."""
    result1: int = 0
    result2: int = 0

    # Run comprehensions benchmark 100 times
    for i in range(100):
        result1 = set_comprehensions()

    # Run basic operations benchmark 100 times
    for i in range(100):
        result2 = set_operations()

    # Print combined result
    print(result1 + result2)

    return 0
