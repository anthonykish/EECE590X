"""
bits.py

Utility functions for working with binary bitstrings.

This module provides helpers for:
- converting integers to binary
- converting binary to integers
- validating bitstrings
- splitting and joining bit sequences
- generating all binary combinations
- validating truth table properties

These utilities are used by FSM conversion logic in convert.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Union

BitLike = Union[int, str]


def int_to_bits(value: int, width: int) -> str:
    """
    Convert an integer into a fixed-width binary string.

    Parameters
    ----------
    value : int
        Non-negative integer to convert.
    width : int
        Number of bits in the resulting string.

    Returns
    -------
    str
        Binary string of length `width`.

    Example
    -------
    >>> int_to_bits(5, 4)
    '0101'
    """
    if value < 0:
        raise ValueError("value must be non-negative")
    if value >= (1 << width):
        raise ValueError("value does not fit in specified width")

    return format(value, f"0{width}b")


def bits_to_int(bits: str) -> int:
    """
    Convert a binary string into an integer.

    Parameters
    ----------
    bits : str
        Bitstring containing only 0s and 1s.

    Returns
    -------
    int
        Integer value of the binary string.

    Example
    -------
    >>> bits_to_int("0101")
    5
    """
    bits = bits.replace("_", "").replace(" ", "")
    if any(c not in "01" for c in bits):
        raise ValueError("invalid bitstring")
    return int(bits, 2)


def normalize_bits(value: BitLike, width: int) -> str:
    """
    Normalize input into a fixed-width bitstring.

    Accepts integers or binary/hex strings and converts them into
    a binary string of length `width`.

    Parameters
    ----------
    value : int or str
        Input value to normalize.
    width : int
        Expected width of the output bitstring.

    Returns
    -------
    str
        Binary string of length `width`.

    Example
    -------
    >>> normalize_bits(5, 4)
    '0101'

    >>> normalize_bits("0xA", 4)
    '1010'
    """
    if isinstance(value, int):
        return int_to_bits(value, width)

    s = value.strip()

    if s.startswith("0x"):
        return int_to_bits(int(s, 16), width)

    if s.startswith("0b"):
        s = s[2:]

    if len(s) != width:
        raise ValueError("bitstring has incorrect width")

    if any(c not in "01" for c in s):
        raise ValueError("invalid characters in bitstring")

    return s


def concat_bits(*parts: str) -> str:
    """
    Concatenate multiple bitstrings into one.

    Parameters
    ----------
    parts : str
        Bitstrings to concatenate.

    Returns
    -------
    str
        Combined bitstring.

    Example
    -------
    >>> concat_bits("10", "11")
    '1011'
    """
    return "".join(parts)


def split_bits(bits: str, *widths: int) -> tuple[str, ...]:
    """
    Split a bitstring into multiple segments.

    Parameters
    ----------
    bits : str
        Bitstring to split.
    widths : int
        Width of each resulting segment.

    Returns
    -------
    tuple[str]
        Segments of the original bitstring.

    Example
    -------
    >>> split_bits("001011", 2,1,3)
    ('00','1','011')
    """
    i = 0
    result = []
    for w in widths:
        result.append(bits[i:i+w])
        i += w
    return tuple(result)


def all_bitstrings(width: int) -> Iterator[str]:
    """
    Generate all bitstrings of length `width`.

    Parameters
    ----------
    width : int
        Length of the bitstrings.

    Returns
    -------
    iterator[str]

    Example
    -------
    >>> list(all_bitstrings(2))
    ['00','01','10','11']
    """
    for i in range(1 << width):
        yield int_to_bits(i, width)


def sort_bitstrings(bitstrings: Iterable[str]) -> list[str]:
    """
    Sort bitstrings by numeric value.

    Parameters
    ----------
    bitstrings : iterable[str]

    Returns
    -------
    list[str]

    Example
    -------
    >>> sort_bitstrings(["10","01","00"])
    ['00','01','10']
    """
    return sorted(bitstrings, key=lambda b: int(b, 2))


def validate_bitstring(bits: str, width: Optional[int] = None) -> str:
    """
    Validate a bitstring.

    Parameters
    ----------
    bits : str
        Bitstring to validate.
    width : int, optional
        Expected width.

    Returns
    -------
    str
        Cleaned bitstring.

    Example
    -------
    >>> validate_bitstring("0101",4)
    '0101'
    """
    bits = bits.replace("_", "").replace(" ", "")
    if any(c not in "01" for c in bits):
        raise ValueError("invalid bitstring")

    if width is not None and len(bits) != width:
        raise ValueError("incorrect width")

    return bits


def validate_table_complete(n_rows: int, input_width: int) -> None:
    """
    Verify that a truth table contains all input combinations.

    Parameters
    ----------
    n_rows : int
        Number of rows in the table.
    input_width : int
        Number of input bits.

    Example
    -------
    >>> validate_table_complete(8,3)
    (valid because 2^3 = 8)
    """
    if n_rows != 2 ** input_width:
        raise ValueError("truth table incomplete")


def ensure_unique_keys(keys: Iterable[str]) -> None:
    """
    Ensure that all keys in an iterable are unique.

    Parameters
    ----------
    keys : iterable[str]

    Example
    -------
    >>> ensure_unique_keys(["00","01","10"])
    (valid)

    >>> ensure_unique_keys(["00","01","00"])
    ValueError
    """
    seen = set()
    for k in keys:
        if k in seen:
            raise ValueError("duplicate key detected")
        seen.add(k)


@dataclass(frozen=True, slots=True)
class Widths:
    """
    Container describing FSM widths.

    Attributes
    ----------
    k_state : int
        Number of state bits.
    m_in : int
        Number of input bits.
    p_out : int
        Number of output bits.

    Example
    -------
    >>> w = Widths(2,2,1)
    >>> w.truth_in_width
    4
    """
    k_state: int
    m_in: int
    p_out: int

    @property
    def truth_in_width(self) -> int:
        return self.k_state + self.m_in

    @property
    def truth_out_width(self) -> int:
        return self.k_state + self.p_out