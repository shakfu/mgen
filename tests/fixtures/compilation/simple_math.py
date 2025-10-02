"""Simple math operations test - should work on all backends."""


def add(a: int, b: int) -> int:
    return a + b


def multiply(x: int, y: int) -> int:
    return x * y


def main() -> int:
    result: int = add(5, 3)
    product: int = multiply(result, 2)
    print(product)  # Should print 16
    return 0
