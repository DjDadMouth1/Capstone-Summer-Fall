from frictionless import errors

class DuplicateRowError(errors.RowError):
    code = "duplicate-row"
    name = "Duplicate Row"
    tags = ["#table", "#row", "#duplicate"]
    template = "Row at position {rowPosition} is duplicated: {note}"
    description = "The row is duplicated."
    
class HeaderFormatError(errors.HeaderError):
    code = "header-format-error"
    name = "Header Format Error"
    tags = ["#table", "#header", "#format"]
    template = "At position {fieldPosition} does not follow the Column Name Format: {note}"
    description = "column names must be all upper case and limited to 30 characters and must start with an alphabetic character. Use only alphanumeric characters and period (.), dash(-) or underscore (_)."
    
class NumericFieldError(errors.CellError):
    code = "numeric-field-error"
    name = "Numeric Field Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "This cell contains a mix of both text and numeric characters. Do not mix text in a field that is intended to contain numeric or date data."
    
class ZipCodeConsistencyError(errors.CellError):
    code = "zip-code-consistency-error"
    name = "Zip Codes Inconsistent"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Zip code format in this cell is inconsistent with other zip codes in this dataset. Zip Codes Five-digit or nine-digit Zip Codes are acceptable. Consistency within a dataset is critical. Nine-digit Zip Codes can be provided as hyphenated values (i.e.12345-9876)"

class ZipCodeFormatError(errors.CellError):
    code = "zip-code-format-error"
    name = "Zip Code Format Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Zip code in this cell is does not conform to ZIP CODE statndatds. Only five-digit or nine-digit Zip Codes are acceptable. Consistency within a dataset is critical. Nine-digit Zip Codes can be provided as hyphenated values (i.e.12345-9876)"
    