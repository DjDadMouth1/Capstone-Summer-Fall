from frictionless import errors

class HeaderFormatError(errors.GeneralError):
    code = "header-format-error"
    name = "Header Format Error"
    tags = ["#table", "#header", "#format"]
    template = "{note}"
    description = "Column names must be all upper case and limited to 30 characters and must start with an alphabetic character. Use only alphanumeric characters and period (.), dash(-) or underscore (_)."
    
class NumericFieldError(errors.CellError):
    code = "numeric-field-error"
    name = "Numeric Field contains special characters"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "This cell contains a mix of both text and numeric characters. Do not mix text in a field that is intended to contain numeric or date data."
    
    
class ZipCodeFormatError(errors.CellError):
    code = "zip-code-format-error"
    name = "Zip Code Format Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldName}: {note}"
    description = "Zip code in this cell is does not conform to ZIP CODE statndatds. Only five-digit or nine-digit Zip Codes are acceptable. Consistency within a dataset is critical. Nine-digit Zip Codes can be provided as hyphenated values (i.e.12345-9876)"
    

class ZipCodeFormatConsistencyError(errors.CellError):
    code = "zip-code-consistency-error"
    name = "Zip Codes Inconsistent"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Zip code format in this cell is inconsistent with other zip codes in this column. Zip Codes Five-digit or nine-digit Zip Codes are acceptable. Consistency within a dataset is critical. Nine-digit Zip Codes can be provided as hyphenated values (i.e.12345-9876)"
    

class PhoneNumberFormatError(errors.CellError):
    code = "phone-number-format-error"
    name = "Phone Number Format Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Phone number in this cell does not conform to phone number format standard. Phone numbers must be ten digits, include the area code, and be separated by hyphens (-) (i.e.XXX-XXX-XXXX)."


class BooleanFormatConsistencyError(errors.CellError):
    code = "boolean-consistency-error"
    name = "Boolean data Inconsistent"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = 'Boolean format in this cell is inconsistent with other boolean values in this column. Only one of the following sets of boolean values may be used per column: [{"1","0"}, {"t", "f"}, {"true", "false"}, {"yes", "no"}, {"y", "n"}, {"on", "off"}] ()'
    
#JORDAN'S SECTION
class LeadTrailWhitespace(errors.ConstraintError):
    code = "leading-or-trailing-whitespace"
    name = "Leading or Trailing Whitespace"
    tags = ["#table", "#row", "#cell"]
    template = 'The cell "{cell}" in row "{rowPosition}" at position "{fieldPosition}" does not conform to a constraint: {note}'
    description = "The field value contains leading or trailing whitespace"


class AddressFieldSeperated(errors.HeaderError):
    code = "address-field-seperated"
    name = "Address Field Seperated"
    tags = ["#table", "#header", "#label"]
    template = "The address fields should not be seperated: {note}"
    description = "Address fields should be combined into one field"

class MonetaryFields(errors.ConstraintError):
    code = "monetary-fields"
    name = "Monetary Fields"
    tags = ["#table", "#row", "#cell"]
    template = 'The cell "{cell}" in row "{rowPosition}" at position "{fieldPosition}" does not conform to a constraint: {note}'
    description = "The field value contains a monetary value that shold not have '$' or ',' characters"