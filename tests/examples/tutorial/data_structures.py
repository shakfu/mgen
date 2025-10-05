"""Data structures in Go."""


def create_list() -> list[int]:
    """Create and populate a list."""
    scores: list[int] = []
    scores.append(95)
    scores.append(87)
    scores.append(92)
    return scores


def find_max(scores: list[int]) -> int:
    """Find maximum score."""
    max_score: int = 0
    for score in scores:
        if score > max_score:
            max_score = score
    return max_score


def main() -> int:
    """Main function."""
    scores: list[int] = create_list()
    max_score: int = find_max(scores)
    print(max_score)
    return 0
