"""Test 2D list as function parameter."""


def sum_matrix(data: list) -> int:
    """Sum all elements in 2D matrix."""
    total: int = 0
    for i in range(3):
        for j in range(3):
            total += data[i][j]
    return total


def main() -> int:
    """Create matrix and sum it."""
    matrix: list = []
    for i in range(3):
        row: list = []
        for j in range(3):
            row.append(i + j)
        matrix.append(row)

    result: int = sum_matrix(matrix)
    print(result)
    return 0
