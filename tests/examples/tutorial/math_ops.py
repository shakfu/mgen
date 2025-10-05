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
