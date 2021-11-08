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

class PhoneNumberFormatError(errors.CellError):
    code = "phone-number-format-error"
    name = "Phone Number Format Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Phone number in this cell does not conform to phone number format standard. Phone numbers must be ten digits, include the area code, and be separated by hyphens (-) (i.e.XXX-XXX-XXXX)."
    
class WebLinkFormatError(errors.CellError):
    code = "web-link-format-error"
    name = "Web Link Format Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Web link in this cell does not conform to web link format standard. Web links need to be stored in a field named URL, must begin with http:// or https://, and have the following HTML style: <a href=\"https://www.example.com/\">An example website</a>"
    
class GeolocationFormatError(errors.CellError):
    code = "geolocation-format-error"
    name = "Geolocation Format Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Geolocation in this cell does not conform to geolocation format standard. Latitude must be between 90 and -90 degrees and longitude must be between 180 and -180 degrees. Latitude and longitude must either be stored in two seperate fields or stored in a single point field with the format: POINT(longitude latitude)"
    
class LogDateMatchError(errors.CellError):
    code = "log-date-match-error"
    name = "Log Date Match Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Log date in this cell does not conform to log date standard. Record date marks the time the data is collected. Log date differs from it as it marks the time the data is uploaded. They should not match."
    
class BureauCodeMatchError(errors.CellError):
    code = "bureau-code-match-error"
    name = "Bureau Code Match Error"
    tags = ["#table", "#row", "#cell"]
    template = "Row at position {rowPosition} and field at position {fieldPosition}: {note}"
    description = "Data in this cell does not conform to bureau code standard. Bureau must exist and bureau code must match bureau description."
    