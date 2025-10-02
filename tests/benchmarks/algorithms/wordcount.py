"""Word count benchmark - String and dictionary operations performance."""


def count_words(text: str) -> dict:
    """Count word frequencies in text."""
    # Split text into words
    words: list = text.split()

    # Count word frequencies
    word_counts: dict = {}
    for word in words:
        # Convert to lowercase and strip
        clean_word: str = word.lower().strip()

        # Update count
        if clean_word in word_counts:
            word_counts[clean_word] = word_counts[clean_word] + 1
        else:
            word_counts[clean_word] = 1

    return word_counts


def main() -> int:
    """Run word count benchmark."""
    # Sample text with repeated words
    text: str = "the quick brown fox jumps over the lazy dog the fox is quick and the dog is lazy"

    # Count words multiple times for benchmarking
    result: dict = {}
    for iteration in range(1000):
        result = count_words(text)

    # Print count of most common word
    the_count: int = 0
    if "the" in result:
        the_count = result["the"]

    print(the_count)

    return 0
