"""Fibonacci benchmark - Recursive algorithm performance."""


def fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def main() -> int:
    """Run Fibonacci benchmark."""
    # Calculate Fibonacci numbers up to n=30
    result: int = 0
    for i in range(30):
        result = fibonacci(i)

    # Print final result
    print(result)
    return 0
