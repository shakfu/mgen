"""Test returning 2D list from function."""


def create_identity(size: int) -> list:
    """Create identity matrix."""
    result: list = []
    for i in range(size):
        row: list = []
        for j in range(size):
            if i == j:
                row.append(1)
            else:
                row.append(0)
        result.append(row)
    return result


def main() -> int:
    """Test identity matrix creation."""
    matrix: list = create_identity(3)
    print(matrix[0][0])
    print(matrix[1][1])
    print(matrix[0][1])
    return 0
