"""Quicksort benchmark - Functional recursive implementation."""


def quicksort(arr: list) -> list:
    """Sort array using functional quicksort algorithm."""
    if len(arr) <= 1:
        return arr

    # Use first element as pivot
    pivot: int = arr[0]
    rest: list = arr[1:]

    # Partition into less and greater lists
    less: list = [x for x in rest if x < pivot]
    greater: list = [x for x in rest if x >= pivot]

    # Recursively sort and concatenate
    return quicksort(less) + [pivot] + quicksort(greater)


def main() -> int:
    """Run quicksort benchmark."""
    # Create array with numbers in reverse order and sort it
    arr: list[int] = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55,
                      50, 45, 40, 35, 30, 25, 20, 15, 10, 5]

    sorted_arr: list[int] = quicksort(arr)
    print(sorted_arr[0])

    return 0
