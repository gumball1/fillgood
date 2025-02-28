# -*- coding: utf-8 -*-

"""
    FanFilm Add-on

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import re
import unicodedata
from itertools import tee
from typing import Optional, TypeVar, Iterable, Generator, Dict, Set

#: Just a type.
T = TypeVar('T')


# robson (Tue, 20 Dec 2022), MIT
def pairprev(iterable: Iterable[T], fillvalue: Optional[T] = None) -> Generator[T, None, None]:
    "s -> (None,s0), (s0,s1), (s1,s2), ..."
    a, b = tee(iterable)
    try:
        yield fillvalue, next(b)
    except StopIteration:
        return
    yield from zip(a, b)


#: `slugify_latin()` letter name regex (nedded for "Łł")
slugify_latin_rx: re.Pattern = re.compile(r'LATIN (?P<case>CAPITAL|SMALL) LETTER \b(?P<ch>.)\b')


# robson (Tue, 20 Dec 2022), MIT
def remove_invisible_chars(string: str) -> str:
    """
    Remove non-visible chars like zero-width space.
    """
    return re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]', '', string)


# robson (Tue, 20 Dec 2022), MIT
def slugify_latin(string: str, *, punctation: bool = True) -> str:
    """Skip accents in latin strings."""
    def handle(ch: str) -> str:
        uname: str = unicodedata.name(ch)
        m: re.Match = slugify_latin_rx.match(uname)
        if m:
            ch = m['ch']
            if m['case'] == 'SMALL':
                ch = ch.lower()
            return ch
        if 'SPACE' in uname:
            return ' '
        if 'DASH' in uname or 'HORIZONTAL BAR' in uname:
            return '-'
        if 'VERTICAL BAR' in uname:
            return '|'
        if 'QUOTATION MARK' in uname:
            return '"'
        if 'BULLET' in uname or 'ELLIPSIS' in uname:
            return '.'
        return ch

    if punctation:
        string = remove_invisible_chars(string)
    string = unicodedata.normalize('NFKD', string)
    string = ''.join(ch if ord(ch) < 128 else handle(ch) for ch in string if unicodedata.category(ch) != 'Mn')
    if punctation:
        # replace multiple spaces, dots, hypens to single one
        string = re.sub(r'([-. ])+', r'\1', string)
    return string


#: remove
crush_prefixes: Set[str] = {
    'a', 'af',
    'd', 'de', 'di',
    'ier',
    'of',
    'saint', 'sainte',
    'van', 'von',
    'zu', 'zur',
    'the', 'a', 'an',
    'der', 'die', 'das',
}

#: `crush()` replace regex.
crush_rx: re.Pattern = re.compile(rf'\b({"|".join(crush_prefixes)})\b'
                                  r'|(?P<first_vowel>\b[aeiouy])|(ph|s\b|[kqzhaeiouy])')


# robson (Tue, 20 Dec 2022), MIT
def crush_name(name: str) -> str:
    """
    A geneweb sonnex/soundex-like phonetic algorithm.

    - no spaces
    - roman numbers are keeped
    - vowels are suppressed, except in words starting with a vowel, where this vowel is converted into "e"
    - "k" and "q" replaced by "c"
    - "z" replaced by "s"
    - "ph" replaced by "f"
    - others "h" deleted
    - s at end of words are deleted
    - no double lowercase consons

    See: https://geneweb.github.io/geneweb/geneweb/Name/index.html#val-crush
    """
    def replace(m: re.Match) -> str:
        if m.group('first_vowel'):  # words starting with a vowel
            return 'e'
        return rpr.get(m.group(0), '')

    rpr: Dict[str, str] = {
        'k': 'c',
        'q': 'c',
        'z': 's',
    }
    out: str = crush_rx.sub(replace, name.lower())
    out = ''.join('' if p == c else c for p, c in pairprev(out))
    return re.sub(r'\s*', '', out)


# robson (Tue, 20 Dec 2022), MIT
def soundex(name: str, *, length: int = 4, full: bool = False) -> str:
    """
    Phonetic Algorithm Soundex

    Soundex algorithm is used for encoding English words on the basis of their sound. The main purpose is to avoid
    spelling errors when recording the names of people in a census. Source code can be presented as a code of
    4 characters in the form LDDD, where L is the first letter of the name and D represents a decimal digit
    (for English alphabet D is in the range of 0 to 6).

    See: https://open4tech.com/phonetic-algorithm-soundex/
    """
    if not name:
        return '0000'
    name = name.upper()
    # 1. The first character code is always the first letter of the name, regardless of other rules.
    out: str = name[0]
    pc: str = ''
    skip: bool = False
    for i, c in enumerate(name[1:], 1):
        # 9. If there are two repeated letters, the second is skipped.
        if pc == c:
            continue
        code = ''
        # 3. The letters “B”, “F”, “P” and “V” are coded as 1.
        if c in 'BFPV':
            code = '1'
        # 4. The letters “C”, “G”, “J”, “K”, “Q”, “S”, “X” and “Z” are coded as 2.
        elif c in 'CGJKQSXZ':
            code = '2'
        # 5. Letter “D” and “T” are coded as 3.
        elif c in 'DT':
            code = '3'
        # 6. The letter “L” is coded as 4.
        elif c in 'L':
            code = '4'
        # 7. The letters “M” and “N” are coded as 5.
        elif c in 'MN':
            code = '5'
        # 8. The letter “R” is coded as 6.
        elif c in 'R':
            code = '6'
        #  2. The letters “A”, “E”, “I”, “O”, “U”, “H”, “W” and “Y” are released.
        # 13. Letters with the same code separated by “H” or “W” are not coded.
        elif c in 'HW':
            continue
        #  2. The letters “A”, “E”, “I”, “O”, “U”, “H”, “W” and “Y” are released.
        # 12. Letters with the same code separated by “A”, “E”, “I”, “O” or “U” are coded.
        else:
            skip = True
        # 10. If any letter has the same code as the previous, it is skipped. Except the rule 12.
        if code and (skip or code != out[-1]):
            out += code
            skip = False
        pc = c
    # 14. If characters in the end code are less than four are supplemented with 0 to four.
    out = out.ljust(length, '0')
    if full:
        return out
    # Source code can be presented as a code of 4 characters in the form LDDD
    return out[:length]


def json_load_as_str(file_handle):
    return byteify(json.load(file_handle, object_hook=byteify), ignore_dicts=True)


def json_loads_as_str(json_text):
    return byteify(json.loads(json_text, object_hook=byteify), ignore_dicts=True)


def byteify(data, ignore_dicts=False):
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return dict(
            [
                (byteify(key, ignore_dicts=True), byteify(value, ignore_dicts=True))
                for key, value in data.items()
            ]
        )
    return data


def title_key(title):
    try:
        if title is None:
            title = ""
        articles_en = ["the", "a", "an"]
        articles_de = ["der", "die", "das"]
        articles = articles_en + articles_de

        match = re.match(r"^((\w+)\s+)", title.lower())
        if match and match.group(2) in articles:
            offset = len(match.group(1))
        else:
            offset = 0

        return title[offset:]
    except:
        return title


def convert(data):
    if isinstance(data, bytes):
        return data.decode()
    if isinstance(data, (str, int)):
        return str(data)
    if isinstance(data, dict):
        return dict(map(convert, data.items()))
    if isinstance(data, tuple):
        return tuple(map(convert, data))
    if isinstance(data, list):
        return list(map(convert, data))
    if isinstance(data, set):
        return set(map(convert, data))
    else:
        return data
