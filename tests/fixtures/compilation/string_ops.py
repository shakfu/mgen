"""String operations test - should work on all backends."""


def process_string(text: str) -> str:
    upper: str = text.upper()
    return upper


def main() -> int:
    result: str = process_string("hello")
    print(result)  # Should print HELLO
    return 0
