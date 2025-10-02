"""Matrix multiplication benchmark - Numeric computation performance."""


def create_matrix(rows: int, cols: int, value: int) -> list:
    """Create a matrix filled with a value."""
    matrix: list = []
    for i in range(rows):
        row: list = []
        for j in range(cols):
            row.append(value)
        matrix.append(row)
    return matrix


def matrix_multiply(a: list, b: list, size: int) -> list:
    """Multiply two square matrices."""
    result: list = create_matrix(size, size, 0)

    for i in range(size):
        for j in range(size):
            sum_val: int = 0
            for k in range(size):
                sum_val += a[i][k] * b[k][j]
            result[i][j] = sum_val

    return result


def main() -> int:
    """Run matrix multiplication benchmark."""
    # Create two 20x20 matrices
    size: int = 20
    matrix_a: list = create_matrix(size, size, 2)
    matrix_b: list = create_matrix(size, size, 3)

    # Multiply matrices 10 times for benchmarking
    result: list = []
    for iteration in range(10):
        result = matrix_multiply(matrix_a, matrix_b, size)

    # Print result from center of matrix
    center: int = size // 2
    print(result[center][center])

    return 0
