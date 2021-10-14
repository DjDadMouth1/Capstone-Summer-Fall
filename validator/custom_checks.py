from frictionless import Check, errors
import errors
"""
Portland State Capstone Team C - Open Data PDX
Validator Custom Checks
"""

"""
LEADING OR TRAILING SPACES

Checks each value for leading or trailing
whitespace
"""

class lead_trail_spaces(Check):
    code = "leading-or-trailing-whitespace"
    Errors = [errors.LeadTrailWhitespace]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
    
    def validate_row(self, row):
        for cell in row.items():
            if cell is None:
                continue

            if cell != cell.strip():
                note = "value has leading or trailing whitespace"
                yield errors.LeadTrailWhitespace.from_row(row, note=note)

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }