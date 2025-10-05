"""String operations in Rust."""


def count_words(text: str) -> int:
    """Count words in a string."""
    words: list[str] = text.split()
    return len(words)


def to_uppercase(text: str) -> str:
    """Convert string to uppercase."""
    return text.upper()


def main() -> int:
    """Main function."""
    sentence: str = "hello rust from python"
    word_count: int = count_words(sentence)
    upper: str = to_uppercase(sentence)

    print(word_count)
    print(upper)
    return 0
