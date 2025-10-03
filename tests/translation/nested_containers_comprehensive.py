"""Comprehensive test suite for nested container patterns."""


def test_2d_list_basic() -> int:
    """Test basic 2D list creation and access."""
    matrix: list = []
    for i in range(3):
        row: list = []
        for j in range(3):
            row.append(i * 3 + j)
        matrix.append(row)
    return matrix[1][1]


def test_2d_list_function_params(data: list) -> int:
    """Test 2D list as function parameter."""
    total: int = 0
    for i in range(len(data)):
        for j in range(len(data[i])):
            total += data[i][j]
    return total


def test_2d_list_function_return() -> list:
    """Test returning 2D list from function."""
    result: list = []
    for i in range(2):
        row: list = []
        for j in range(2):
            row.append(i + j)
        result.append(row)
    return result


def test_2d_list_assignment() -> int:
    """Test 2D list element assignment."""
    grid: list = []
    for i in range(3):
        row: list = []
        for j in range(3):
            row.append(0)
        grid.append(row)

    grid[0][0] = 10
    grid[1][1] = 20
    grid[2][2] = 30
    return grid[1][1]


def test_nested_list_comprehension_simulation() -> int:
    """Test nested list operations (simulating comprehension)."""
    numbers: list = []
    for i in range(3):
        row: list = []
        for j in range(3):
            if (i + j) % 2 == 0:
                row.append(i * j)
        numbers.append(row)

    count: int = 0
    for row in numbers:
        count += len(row)
    return count


def test_matrix_multiplication_mini() -> int:
    """Mini matrix multiplication (2x2)."""
    a: list = []
    b: list = []

    for i in range(2):
        row_a: list = []
        row_b: list = []
        for j in range(2):
            row_a.append(i + 1)
            row_b.append(j + 1)
        a.append(row_a)
        b.append(row_b)

    result: list = []
    for i in range(2):
        row: list = []
        for j in range(2):
            sum_val: int = 0
            for k in range(2):
                sum_val += a[i][k] * b[k][j]
            row.append(sum_val)
        result.append(row)

    return result[0][0]


def main() -> int:
    """Run all nested container tests."""
    # Test 1: Basic 2D access
    val1: int = test_2d_list_basic()
    print(val1)

    # Test 2: Function parameters
    test_data: list = []
    for i in range(2):
        row: list = []
        for j in range(2):
            row.append(i + j)
        test_data.append(row)
    val2: int = test_2d_list_function_params(test_data)
    print(val2)

    # Test 3: Function return
    returned: list = test_2d_list_function_return()
    print(len(returned))

    # Test 4: Assignment
    val4: int = test_2d_list_assignment()
    print(val4)

    # Test 5: Nested operations
    val5: int = test_nested_list_comprehension_simulation()
    print(val5)

    # Test 6: Matrix multiplication
    val6: int = test_matrix_multiplication_mini()
    print(val6)

    return 0
