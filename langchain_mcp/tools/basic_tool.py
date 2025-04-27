# string based tools
def reverse_string(string: str) -> str:
    return string[::-1]


def count_words(string: str) -> int:
    return len(string.split())


def is_palindrome(string: str) -> bool:
    return string == string[::-1]


def count_vowels(string: str) -> int:
    return sum(1 for char in string if char.lower() in "aeiou")


def count_consonants(string: str) -> int:
    return sum(1 for char in string if char.lower() in "bcdfghjklmnpqrstvwxyz")


# number based tools
def add_numbers(a: int, b: int) -> int:
    return a + b


def subtract_numbers(a: int, b: int) -> int:
    return a - b


def multiply_numbers(a: int, b: int) -> int:
    return a * b


def divide_numbers(a: int, b: int) -> float:
    return a / b


def square_number(a: int) -> int:
    return a * a


def cube_number(a: int) -> int:
    return a * a * a


def is_even(a: int) -> bool:
    return a % 2 == 0


def is_odd(a: int) -> bool:
    return a % 2 != 0


def is_prime(a: int) -> bool:
    if a <= 1:
        return False
    for i in range(2, a):
        if a % i == 0:
            return False
