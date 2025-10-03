"""Simple 2D nested container test."""


def main() -> int:
    """Test basic 2D list operations."""
    matrix: list = []
    for i in range(3):
        row: list = []
        for j in range(3):
            row.append(i * 3 + j)
        matrix.append(row)

    # Test read
    val: int = matrix[1][1]
    print(val)

    # Test write
    matrix[2][2] = 99
    print(matrix[2][2])

    return 0
