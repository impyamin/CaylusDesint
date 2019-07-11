#!/usr/bin/python
from enum import Enum, unique


TXT_SEPARATOR = ', '  # type: str # Separator between two elements of an enumeration of string elements.


def ordinal_number(n: int) -> str:
    """Get the ordinal number."""
    if n <= 0:
        raise Exception('The ordinal number is not defined for non-positive integers.')
    else:
        digit = n % 10  # type: int
        letter_suffix = None  # type: str
        if digit == 1:
            letter_suffix = 'st'
        elif digit == 2:
            letter_suffix = 'nd'
        elif digit == 3:
            letter_suffix = 'rd'
        else:
            letter_suffix = 'th'
        return str(n) + letter_suffix


def indent(n_indent: int) -> str:
    """Get a string in order to create an indentation."""
    return '  ' * n_indent


@unique
class Location(Enum):
    """Enumeration of all the possible locations of the player buildings."""
    HAND = 0
    PILE = 1
    DISCARD = 2
    ROAD = 3
    REPLACED = 4
