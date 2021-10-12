from pprint import pprint
from frictionless import Check, errors, validate
import hashlib


class LowercaseCharHeaderError(errors.HeaderError):
    code = "lowercase-character"
    name = "Lowercase Header"
    tags = ["#table", "#header", "#lowercase"]
    template = "Header at position {rowPosition} has a lowercase character: {note}"
    description = "Lowercase character in the header. All characters in the header must be uppercase"


class lowercase_char_header(Check):
    code = "lowercase-character"
    Errors = [errors.LowercaseCharHeaderError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def check_header_is_uppercase(self, row):
        for label in row:
            if not label.isupper():
                note = 'lowercase char in header at position "%s"' % label
                yield errors.lowercase_char_header.from_row(row, note=note)


    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }