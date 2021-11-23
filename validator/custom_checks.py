from frictionless import Check, errors
from .custom_errors import *
from sqlalchemy.sql.expression import false
from datetime import datetime
import re


class header_format(Check):
    """
    Open Data Handbook Reference - Column Names

    Checks System column names must be all upper case and limited to 30 characters and must start with an alphabetic character. 
    Use only alphanumeric characters and period (.), dash(-) or underscore (_). Avoid use of abbreviations. Instead, use the 
    title case for field names and be sure that the names match that in the Data Dictionary. Aliases reflect real-world context,
    use simple language, names limited to 30 characters, initcaps words and spaces to separate words.
    """
    code = "header-format-error"
    Errors = [HeaderFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__errors = []

    def validate_start(self):
        MAX_CHARACTERS = 30

        # get header data
        header_data = self.resource.header
        labels = header_data.labels
        fields = header_data.fields
        field_positions = header_data.field_positions

        # Iterate through each header name and check if the name meets the PDX Opendata requirements.
        field_number = 0
        for field_position, field, label in zip(field_positions, fields, labels):

            # check PDX Opendata requirements
            field_name_errors_note = []
            is_first_letter_alphabetic = label[0].isalpha()
            is_numeric = (
                label.replace(".", "").replace("-", "").replace("_", "").isalnum()
            )
            is_uppercase = label.isupper()
            is_less_than_max_length = len(label) <= MAX_CHARACTERS

            # Put together the error message for the column name
            error_position_msg = f"The column name, '{label}', at field position {field_position} has the following error(s): "
            field_name_errors_note.append(error_position_msg)
            if not is_first_letter_alphabetic:
                field_name_errors_note.append("The first character is not alphabetic ")
            if not is_numeric:
                if len(field_name_errors_note) < 2:
                    field_name_errors_note.append(
                        "It contains non-alphanumeric character(s) "
                    )
                else:
                    field_name_errors_note.append(
                        ", it contains non-numeric character(s) "
                    )
            if not is_uppercase:
                if len(field_name_errors_note) < 2:
                    field_name_errors_note.append("It contains lowercase character(s)")
                else:
                    field_name_errors_note.append(
                        ", it contains lowercase character(s)"
                    )
            if not is_less_than_max_length:
                if len(field_name_errors_note) < 2:
                    field_name_errors_note.append("Exceeds 30 characters limit")
                else:
                    field_name_errors_note.append(", exceeds 30 characters limit")
            note_length = len(field_name_errors_note)
            if note_length > 2:
                last_message = field_name_errors_note[-1]
                last_message = last_message.replace(", ", ", and ")
                field_name_errors_note[-1] = last_message
            field_name_errors_note = "".join(field_name_errors_note)

            # column name does not meet format standards
            if (
                not is_numeric
                or not is_uppercase
                or not is_less_than_max_length
                or not is_first_letter_alphabetic
            ):
                yield HeaderFormatError(note=field_name_errors_note)

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class numeric_field(Check):
    """
    Open Data Handbook Reference - Numeric Field Values

    Checks that text in a field that is intended to contain numeric or date data. Any numerical values, including decimals,
    negatives, or other values without special symbols (%, $, °, etc.). Do not include commas in large number formats.
    """
    code = "numeric-field-error"
    Errors = [NumericFieldError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    # check if there is are numberic fields
    def validate_start(self):
        column_with_numbers = [
            field
            for field in self.resource.schema.fields
            if (field["type"] == "number" or field["type"] == "integer")
        ]
        if not column_with_numbers:
            note = f"Ignore this message if the data does not contain columns containing numbers."
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        # get columns that are numbers
        column_with_numbers = [
            field["name"]
            for field in self.resource.schema.fields
            if (field["type"] == "number" or field["type"] == "integer")
        ]
        # iterate though the columns that are numbers 
        for field_name, field_value in zip(row.field_names, row.cells):
            if field_name in column_with_numbers:
                field_value_string = str(field_value)

                # check if it contains any non-numeric characters (looking for %,$, etc.)
                if not field_value_string.replace(".", "").replace("-", "").replace("'", "").replace('"', "").isalnum():
                    note = f"Data contains special characters. Remove the non-numeric characters from the following value: {field_value_string}."
                    yield NumericFieldError.from_row(
                        row, note=note, field_name=field_name
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class zip_code_format(Check):
    """
    Open Data Handbook Reference - Zip Codes

    Checks for Five-digit or nine-digit Zip Codes are acceptable. Consistency within a dataset is critical. 
    Nine-digit Zip Codes can be provided as hyphenated values (i.e.12345-9876). Do not mix both formats 
    within the same column. Field definitions must be text.
    """
    code = "zip-code-consistency-error"
    Errors = [ZipCodeFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    # check if zip code is in header and get the key
    def validate_start(self):
        ZIP_CODE_KEYS = ["ZIP", "ZIP CODE", "ZIP CODES", "ZIPCODE", "ZIPCODES"]
        actual_zip_code_key = None
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        for zip_code_key in ZIP_CODE_KEYS:
            if zip_code_key in uppercase_headers:
                actual_zip_code_key = zip_code_key
        if not actual_zip_code_key:
            note = f"Ignore this message if the data does not contain ZIP codes"
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        # iterate through row and look for the column with the zipcode 
        for field_name, cell in row.items():
            ZIP_CODE_KEYS = ["ZIP", "ZIP CODE", "ZIP CODES", "ZIPCODE", "ZIPCODES"]
            if field_name.upper() in ZIP_CODE_KEYS:
                # get the zip code value
                zip_code_value = str(cell)
                 # check if zip code meets PDX opendata format
                if not re.search(
                    "^[0-9]{5}-[0-9]{4}$", zip_code_value
                ) and not re.search("^[0-9]{5}$", zip_code_value):
                    note = f"Does not follow ZIP code format. Only 5 digit and hyphenated 9 digit forms are acceptable (for example 97217 or 97217-1202)"
                    yield ZipCodeFormatError.from_row(
                        row, note=note, field_name=field_name
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class zip_code_consistency(Check):
    """
    Open Data Handbook Reference - Zip Codes
    This check ensures columns either use only Five-digit or nine-digit zip codes. 

    Checks for Five-digit or nine-digit Zip Codes are acceptable. Consistency within a dataset is critical. 
    Nine-digit Zip Codes can be provided as hyphenated values (i.e.12345-9876). Do not mix both formats 
    within the same column. Field definitions must be text.
    """
    code = "zip-code-consistency-error"
    Errors = [ZipCodeFormatConsistencyError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    # check if zip code is in header and get the key
    def validate_start(self):
        ZIP_CODE_KEYS = ["ZIP", "ZIP CODE", "ZIP CODES", "ZIPCODE", "ZIPCODES"]
        has_zip_code = False
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        for zip_code_key in ZIP_CODE_KEYS:
            if zip_code_key in uppercase_headers:
                has_zip_code = True
        if not has_zip_code:
            note = f"Ignore this message if the data does not contain ZIP codes"
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        ZIP_CODE_KEYS = ["ZIP", "ZIP CODE", "ZIP CODES", "ZIPCODE", "ZIPCODES"]
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        # Iterate the all fields
        for field_name, cell in row.items():
            # get the field names that are zip codes
            if field_name.upper() in ZIP_CODE_KEYS:
                zip_code_value = str(cell)
                zip_code_length = len(str(cell))
                # check if a current format has been saved for this zip code field.
                saved_zip_code_format = self.__memory.get(field_name)

                # field format not saved yet
                if not saved_zip_code_format:
                    # check if the current zip code meets the PDX opendata format, if not, return error, otherwise save the current format.
                    if not re.search(
                        "^[0-9]{5}-[0-9]{4}$", zip_code_value
                    ) and not re.search("^[0-9]{5}$", zip_code_value):
                        note = f"Does not follow ZIP code format. Only 5 digit and hyphenated 9 digit forms are acceptable (for example 97217 or 97217-1202)"
                        yield ZipCodeFormatError.from_row(
                            row, note=note, field_name=field_name
                        )
                    else:
                        self.__memory[field_name] = (zip_code_length, row.row_position)
                
                # zip code format was found
                if saved_zip_code_format:
                    # check if the current zip code format matches the saved zip code format. If not, yeild error.
                    saved_length = saved_zip_code_format[0]
                    if zip_code_length != saved_length:
                        note = f"Data in {field_name} column is inconsistent. Data does not match format at row posistion {saved_zip_code_format[1]}"
                        yield ZipCodeFormatConsistencyError.from_row(
                            row, note=note, field_name=field_name
                        )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
class boolean_format_consistency(Check):
    """
    Open Data Handbook Reference - Checkboxes
    This check ensures columns using binary data types are conisitent.
    
    Checks for Checkbox and binary values are acceptable formats for a dataset.
    Valid false values: {0, f, false, n, no, off} Valid true values: {1, t, true, y, yes, on}
    """
    code = "boolean-format-consistency-error"
    Errors = [BooleanFormatConsistencyError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    # check if there is are boolean data types in the dataset
    def validate_start(self):
        column_data_types = [field["type"] for field in self.resource.schema.fields]
        if "boolean" not in column_data_types:
            note = f"Ignore this message if the data does not contain boolean columns (True/False)."
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        # current acceptable boolean values by PDX OpenData
        boolean_sets = [
            {"1", "0"},
            {"t", "f"},
            {"true", "false"},
            {"yes", "no"},
            {"y", "n"},
            {"on", "off"},
        ]
        # get the coluns with boolean data
        columns_with_booleans = [
            field["name"]
            for field in self.resource.schema.fields
            if field["type"] == "boolean"
        ]
        # Iterate the all fields
        for field_name, field_value in zip(row.field_names, row.cells):
            # get the fields taht are booleans
            if field_name in columns_with_booleans:
                field_value_string = str(field_value)
                # check if a current format has been saved for this boolean field.
                saved_boolean_format = self.__memory.get(field_name)

                # field boolean format not saved yet
                if not saved_boolean_format:
                    for boolean_set in boolean_sets:
                        # save the current boolean format used
                        if field_value_string in boolean_set:
                            self.__memory[field_name] = (boolean_set, row.row_position)
                # boolean format was found
                if saved_boolean_format:
                    # get the saved boolean format and check if the current boolean format matches
                    # the saved boolean format. If not, yeild error.
                    current_boolean_set = saved_boolean_format[0]
                    if field_value_string not in current_boolean_set:
                        note = f"Boolean data in {field_name} column is not consistent with other boolean values in the column. The current value is {field_value_string} and must be updated ot be one of the following:{current_boolean_set}, which was decided at the following row: {saved_boolean_format[1]}."
                        yield BooleanFormatConsistencyError.from_row(
                            row, note=note, field_name=field_name
                        )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


# JORDAN'S SECTION
class lead_trail_spaces(Check):
    """
    LEADING OR TRAILING SPACES

    Checks each value for leading or trailing
    whitespace
    """

    code = "leading-or-trailing-whitespace"
    Errors = [LeadTrailWhitespace]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    # TODO Check header row
    def validate_row(self, row):

        # cell is a tuple of (field_name, cell value)
        for cell in row.items():
            if not isinstance(cell[1], str):
                continue

            # If strip() removes trail or lead whitespace get the error
            if cell[1] != cell[1].strip():
                note = "value has leading or trailing whitespace"
                yield LeadTrailWhitespace.from_row(row, note=note, field_name=cell[0])

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class address_field_seperate(Check):
    """
    Open Data Handbook Reference - ADDRESS

    Checks for address labels that are seperated to multiple columns by
    Number, Street, Quadrant instead of a single Address field
    """

    code = "address-field-seperated"
    Errors = [AddressFieldSeperated]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_start(self):
        # TODO Fix formatting all caps for constants
        # Keys for possible seperate address field names
        address_labels = ["STREETNUMBER", "STREET", "QUADRANT"]

        # Storage for error labels and positions
        note_fieldnames = []
        note_positions = []

        # Go through all the header labels with their relative positions
        for label, pos in zip(
            self.resource.header.labels, self.resource.header.field_positions
        ):
            # Skip blank labels
            if label is None:
                continue

            # Compare each label to all possible seperate address labels
            for test_label in address_labels:

                # Normalize and compare label
                if label.upper().replace(" ", "") == test_label:
                    note_fieldnames.append(label)
                    note_positions.append(pos)

        # If the list is not empty there is a seperate label error
        if note_fieldnames:
            # Concatenate the label list and produce a single error
            note = f"Fields labeled \"{', '.join(note_fieldnames)}\", should be merged into single \"Address\" label column"
            yield AddressFieldSeperated(
                labels=note_fieldnames, row_positions=note_positions, note=note
            )

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class monetary_fields(Check):
    """
    MONETARY FIELDS

    This may be handled by Numeric Field Values

    Checks monetary fields for '$' or ',' characters
    """

    code = "monetary fields"
    Errors = [MonetaryFields]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        Monetary_Labels = ["COST", "PRICE", "VALUATION"]
        # TODO Fix regex for negatives
        check = re.compile(r"^\d+(\.\d{2})?$")

        # cell is a tuple of (field_name, cell value)
        for cell in row.items():
            print(str(cell[1]) + " type is " + str(type(cell[1])))
            for label in Monetary_Labels:
                if cell[0].upper() == label:

                    # If strip() removes trail or lead whitespace get the error
                    if not bool(check.match(str(cell[1]))):
                        note = "monetary values should only contain numbers to two decimal places, no '$' or commas"
                        yield MonetaryFields.from_row(
                            row, note=note, field_name=cell[0]
                        )

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

# CARL'S SECTION
class phone_number_format_error(Check):
    code = "phone-number-format-error"
    Errors = [PhoneNumberFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        REQUIRED_CHARACTERS = 12
        PHONE_NUMBER_KEYS = [
            "PHONE",
            "PHONE NUMBER",
            "PHONE NUMBERS",
            "PHONENUMBER",
            "PHONENUMBERS",
        ]
        actual_phone_number_key = None
        # check if phone number is in header and get the key
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        for phone_number_key in PHONE_NUMBER_KEYS:
            if phone_number_key in uppercase_headers:
                actual_phone_number_key = phone_number_key
        # if key is found, check the rows
        if actual_phone_number_key:
            phone_number_value = row[actual_phone_number_key]
            phone_number_value_length = len(phone_number_value)
            if not phone_number_value_length == REQUIRED_CHARACTERS:
                note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                yield PhoneNumberFormatError.from_row(
                    row, note=note, field_name=actual_phone_number_key
                )
            # regex search for phone number format 999-999-9999
            # TODO Fix string casting
            elif not re.search("^[0-9]{3}-[0-9]{3}-[0-9]{4}$", phone_number_value):
                note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                yield PhoneNumberFormatError.from_row(
                    row, note=note, field_name=actual_phone_number_key
                )

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class web_link_format_error(Check):
    code = "web-link-format-error"
    Errors = [WebLinkFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        URL_KEY = "URL"
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        # if URL is a data field
        if URL_KEY in uppercase_headers:
            URL_value = row[URL_KEY]
            # regex search for URL format <a href="http://www.example.com">An example website</a>
            # Regex may allow multiple links
            if not re.search('^<a href="(http|https)://\S+">.*</a>$', URL_value):
                note = f"Does not follow web link format. Web links must be written in HTML style, contain only one link, and begin with http:// or https://"
                yield WebLinkFormatError.from_row(row, note=note, field_name=URL_KEY)

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class geolocation_format_error(Check):
    code = "geolocation-format-error"
    Errors = [GeolocationFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        POINT_KEY = "POINT"
        latitude_key = "LATITUDE"
        longitude_key = "LONGITUDE"
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        latitude_value = None
        longitude_value = None
        latitude = None
        longitude = None
        point = None
        # if latitude and longitude are data fields
        if latitude_key in uppercase_headers and longitude_key in uppercase_headers:
            latitude_value = str(row[latitude_key])
            longitude_value = str(row[longitude_key])
        # if point is a data field
        elif POINT_KEY in uppercase_headers:
            point_value = str(row[POINT_KEY])
            if not re.search("^POINT\(\-?[0-9]{1,3}\.[0-9]+ \-?[0-9]{1,2}\.[0-9]+\)$", point_value):
                note = f"Does not follow geolocation format. Point field must be formatted the following way: POINT(longitude latitude)"
                yield GeolocationFormatError.from_row(row, note=note, field_name=POINT_KEY)
            else:
                point = point_value[6:-1]
                point = point.split()
                longitude_value = point[0]
                latitude_value = point[1]
                latitude_key = POINT_KEY
                longitude_key = POINT_KEY
        # if latitude or longitude is a data field but not both
        elif latitude_key in uppercase_headers or longitude_key in uppercase_headers:
            error_key = None
            if latitude_key in uppercase_headers:
                error_key = latitude_key
            if longitude_key in uppercase_headers:
                error_key = longitude_key
            note = f"Does not follow geolocation format. Latitude and longitude fields must both exist"
            yield GeolocationFormatError.from_row(row, note=note, field_name=error_key)
        # latitude and longitude are defined at the same time
        # if defined, check the values
        if latitude_value:
            if not re.search("^\-?[0-9]{1,2}\.[0-9]+$", latitude_value):
                note = f"Does not follow geolocation format. Latitude must be a decimal number"
                yield GeolocationFormatError.from_row(
                    row, note=note, field_name=latitude_key
                )
            elif not re.search("^\-?[0-9]{1,3}\.[0-9]+$", longitude_value):
                note = f"Does not follow geolocation format. Longitude must be a decimal number"
                yield GeolocationFormatError.from_row(
                    row, note=note, field_name=longitude_key
                )
            else:
                latitude = float(latitude_value)
                longitude = float(longitude_value)
                if latitude > 90.0 or latitude < -90.0:
                    note = f"Out of bounds. Latitude must be between 90 and -90 degrees"
                    yield GeolocationFormatError.from_row(
                        row, note=note, field_name=latitude_key
                    )
                if longitude > 180.0 or longitude < -180.0:
                    note = (
                        f"Out of bounds. Longitude must be between 180 and -180 degrees"
                    )
                    yield GeolocationFormatError.from_row(
                        row, note=note, field_name=longitude_key
                    )

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class log_date_match_error(Check):
    code = "log-date-match-error"
    Errors = [LogDateMatchError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        LOG_DATE_KEY = "LOG DATE"
        RECORD_DATE_KEY = "RECORD DATE"
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        if LOG_DATE_KEY in uppercase_headers and RECORD_DATE_KEY in uppercase_headers:
            if str(row[LOG_DATE_KEY]) == str(row[RECORD_DATE_KEY]):
                note = f"Does not follow log date standard. Log date must not match record date"
                yield LogDateMatchError.from_row(
                    row, note=note, field_name=LOG_DATE_KEY
                )

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class bureau_code_match_error(Check):
    code = "bureau-code-match-error"
    Errors = [BureauCodeMatchError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        BUREAU_CODE_KEY = "BUREAU CODE"
        BUREAU_DESCRIPTION_KEY = "BUREAU DESCRIPTION"
        BUREAU_CODES = {
            "boec": "Bureau of Emergency Communications",
            "bfpdr": "Bureau of Fire & Police Disability & Retirement",
            "ppb": "Portland Police Bureau",
            "pfr": "Portland Fire & Rescue",
            "pbem": "Portland Bureau of Emergency Management",
            "ppr": "Portland Parks and Recreation",
            "oca": "Office of the City Attorney",
            "ogr": "Office of Government Relations",
            "omf": "Office of Management and Finance",
            "bhr": "Human Resources",
            "brfs": "Revenue and Financial Services",
            "bts": "Technology Services",
            "cao": "Office of the Chief Administrative Officer",
            "cbo": "City Budget Office",
            "bsa": "Special Appropriations",
            "bes": "Bureau of Environmental Services",
            "pwb": "Portland Water Bureau",
            "bds": "Bureau of Development Services",
            "phb": "Portland Housing Bureau",
            "bps": "Bureau of Planning and Sustainability",
            "oct": "Office for Community Technology",
            "occl": "Office of Community and Civic Life",
            "pcl": "Portland Children's Levy",
            "pp": "Prosper Portland",
            "oehr": "Office of Equity & Human Rights",
            "pbot": "Portland Bureau of Transportation",
            "ocau": "Office of the City Auditor",
            "om": "Office of the Mayor",
            "cpa": "Commissioner of Public Affairs",
            "cps": "Commissioner of Public Safety",
            "cpu": "Commissioner of Public Utilities",
            "cpw": "Commissioner of Public Works",
        }
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        # Don't repeat yourself. There should be a function for this, but Frictionless is weird so I was afraid to try
        if (
            BUREAU_CODE_KEY in uppercase_headers
            and BUREAU_DESCRIPTION_KEY in uppercase_headers
        ):
            if not str(row[BUREAU_CODE_KEY]) in BUREAU_CODES:
                note = f"Does not follow bureau code standard. Bureau code not found"
                yield BureauCodeMatchError.from_row(
                    row, note=note, field_name=BUREAU_CODE_KEY
                )
            elif not str(row[BUREAU_DESCRIPTION_KEY]) in BUREAU_CODES.values():
                note = f"Does not follow bureau code standard. Bureau description not found"
                yield BureauCodeMatchError.from_row(
                    row, note=note, field_name=BUREAU_DESCRIPTION_KEY
                )
            elif (
                not BUREAU_CODES[str(row[BUREAU_CODE_KEY])]
                == row[str(BUREAU_DESCRIPTION_KEY)]
            ):
                note = f"Does not follow bureau code standard. Bureau code must match bureau description"
                yield BureauCodeMatchError.from_row(
                    row, note=note, field_name=BUREAU_CODE_KEY
                )
        elif BUREAU_CODE_KEY in uppercase_headers:
            if not str(row[BUREAU_CODE_KEY]) in BUREAU_CODES:
                note = f"Does not follow bureau code standard. Bureau code not found"
                yield BureauCodeMatchError.from_row(
                    row, note=note, field_name=BUREAU_CODE_KEY
                )
        elif BUREAU_DESCRIPTION_KEY in uppercase_headers:
            if not str(row[BUREAU_DESCRIPTION_KEY]) in BUREAU_CODES.values():
                note = f"Does not follow bureau code standard. Bureau description not found"
                yield BureauCodeMatchError.from_row(
                    row, note=note, field_name=BUREAU_DESCRIPTION_KEY
                )

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


# Faihan's SECTION
"""
This class to check  email format.
"""
class valid_Email_In_Cell(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            if fieldName.upper().find("EMAIL") != -1:  # only run on field name is Email
                cell = str(row[fieldName])
                # slicing domain name using slicing
                isError = False
                if str(cell).find("@") == -1: # Find character "@" to check email format.
                    isError = True
                else:
                    domainName = cell.split("@")[1]
                    # Regex to check valid
                    # domain name.
                    regex = "^((?!-)[A-Za-z0-9-]{1,63}(?<!-)\\.)[A-Za-z]{2,6}"
                    # Compile the ReGex
                    regexCompile = re.compile(regex)
                    if not re.search(regexCompile, domainName):
                        isError = True

                name = cell.split(" ") # find space in email address.
                if len(name) > 1:
                    isError = True

                if isError: # If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not an email"
                    yield errors.CellError.from_row(
                        row, note=note, field_name=fieldName
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Date format.
"""
class valid_Date_In_Cell(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            if fieldName.upper().find("DATE") != -1:  # only run on field name is date
                cell = str(row[fieldName])
                isError = False
                try:
                    date_time_obj = datetime.strptime(cell, "%d/%m/%y") #try to parse this string value into date, if can not past. It mean this cell value is not true Date format
                except:
                    isError = True

                if isError:# If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid date"
                    yield errors.CellError.from_row(
                        row, note=note, field_name=fieldName
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Negative Value format.
"""
class valid_Negative_Value_In_Cell(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            # we only run valid on column have Names are "AMOUNT", "VALUE", "AMT", and "SALARY".
            if (
                (fieldName.upper().find("AMOUNT") != -1)
                or (fieldName.upper().find("VALUE") != -1)
                or (fieldName.upper().find("AMT") != -1)
                or (fieldName.upper().find("SALARY") != -1)
            ):
                cell = str(row[fieldName])
                isError = False
                if cell.upper().find("MINUS") != -1: # find String contain String "MINUS" in cell
                    isError = True
                if (not isError) and (cell.upper().find("SUB") != -1): # find String contain String "SUB" in cell
                    isError = True
                if (not isError) and (cell.upper().find("MINU") != -1):# find String contain String "Minus" in cell
                    isError = True
                if (not isError) and (cell[0].upper().find("(") != -1):# find String contain String "(" in cell
                    isError = True
                if isError:# If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid in Negative Value"
                    yield errors.CellError.from_row(
                        row, note=note, field_name=fieldName
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Name Field format.
"""
class valid_NameField_Value_In_Cell(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            if fieldName.upper().find("NAME") != -1:
                cell = str(row[fieldName])
                # Split the string and get all words in a list
                list_of_words = cell.split()
                isError = False
                for elem in list_of_words:
                    # capitalize first letter of each word and add to a string
                    tmp = elem.strip().capitalize()
                    if tmp != elem: # compare Origin word and capitalize word
                        isError = True # If it is not equal, it mean Error requirement 
                if isError:# If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid Name Field"
                    yield errors.CellError.from_row(
                        row, note=note, field_name=fieldName
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Address format.
"""
class valid_Address_Value_In_Cell(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            if (
                (fieldName.upper().find("ADDRESS") != -1) # only run on field name is ADDRESS
                or (fieldName.upper().find("STATE") != -1) # only run on field name is STATE
                or (fieldName.upper().find("ZIP") != -1) # only run on field name is ZIP
                or (fieldName.upper().find("CITY") != -1) # only run on field name is CITY
            ):
                cell = str(row[fieldName])
                isError = False
                #City State and zip codes should be separated out of the address and stored in separate columns named as CITY, STATE, and ZIPCODE
                if cell.upper().find(",") != -1:  # 'find comma to detect error, 
                    isError = True
                if isError:# If have error, we will set message into Note for Frictionless print into report
                    note = (
                        f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: "
                        f"City State and zip codes should be separated out of the address and stored in separate columns named as CITY, STATE, and ZIPCODE"
                    )
                    yield errors.CellError.from_row(
                        row, note=note, field_name=fieldName
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Text Field format.
"""
class valid_Text_Field_In_Cell(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            if (
                (fieldName.upper().find("AMOUNT") == -1)
                or (fieldName.upper().find("VALUE") == -1)
                or (fieldName.upper().find("AMT") == -1)
                or (fieldName.upper().find("SALARY") == -1)
            ):  # ignore number fields, we only run on String cell
                cell = str(row[fieldName])
                isError = False
                if re.search("<[^/>][^>]*>", cell) != None: # Find html tag in cell String
                    isError = True
                if isError:# If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid in Text Field Value"
                    yield errors.CellError.from_row(
                        row, note=note, field_name=fieldName
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check Data Completeness format.
"""
class valid_Data_Completeness(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            cell = str(row[fieldName])
            isError = False
            if isNotBlank(cell) == False: # run function to detect null value in cell
                isError = True
            if isError:# If have error, we will set message into Note for Frictionless print into report
                note = f"Error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is empty, It is not valid Data Completeness rule"
                yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check Summerized Data format.
"""
class valid_Summerized_Data(Check):
    code = "cell-error"
    Errors = [errors.CellError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            cell = str(row[fieldName])
            isError = False
            if (cell.upper().find("TOT") >= 0) or (cell.upper().find("SUM") >= 0): # only run on field name contains string "TOT" = total and "SUM"
                isError = True
            if isError:# If have error, we will set message into Note for Frictionless print into report
                note = f"Row {rowPosition}: Is including roll-ups, subtotal and total of values in cells as part of the column. It is not valid Summarized Data, applications can compute these values and have totals of subtotals skews results"
                yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

# Function to check Blank value
def isNotBlank(myString):
    if myString and myString.strip():
        # myString is not None AND myString is not empty or blank
        return True
    # myString is None OR myString is empty or blank
    return False
