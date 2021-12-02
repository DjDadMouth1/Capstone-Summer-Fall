from frictionless import Check, errors
from frictionless.errors.label import LabelError
from .custom_errors import *
from sqlalchemy.sql.expression import false, label, true
from datetime import datetime
import re
import importlib.resources as resources


# Load the fields.cfg file into a dictionary with
# the User's custom fields
cfg_dict = {}
cfg_file = resources.open_text('settings', 'fields.cfg')
for line in cfg_file:
    if not line.startswith('#'): 
        key, value = line.rstrip('\n').split(' = ')
        cfg_dict[key] = value.split(',')

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
        self.__checklabels = []
        # Append any new labels from the config file
        if 'ZIP_CODE_FORMAT' in cfg_dict:
            for new_label in cfg_dict['ZIP_CODE_FORMAT']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    # check if zip code is in header and get the key
    def validate_start(self):
        actual_zip_code_key = None
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        for zip_code_key in self.__checklabels:
            if zip_code_key in uppercase_headers:
                actual_zip_code_key = zip_code_key
        if not actual_zip_code_key:
            note = f"zip code format check requires a zip code field:{self.__checklabels}"
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        for field_name, cell in row.items():
            if field_name.upper() in self.__checklabels:
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
        self.__checklabels = []
        # Append any new labels from the config file
        if 'ZIP_CODE_CONSISTENCY' in cfg_dict:
            for new_label in cfg_dict['ZIP_CODE_CONSISTENCY']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    # check if zip code is in header and get the key
    def validate_start(self):
        has_zip_code = False
        uppercase_headers = [
            label.upper() for label in self.resource.schema.field_names
        ]
        for zip_code_key in self.__checklabels:
            if zip_code_key in uppercase_headers:
                has_zip_code = True
        if not has_zip_code:
            note = f"Zip Code consistency check requires one of the following fields to exist:{self.__checklabels} Ignore this message if data does not contain zip codes."
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        for field_name, cell in row.items():
            if field_name.upper() in self.__checklabels:
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
        self.__checklabels = []
        # Append any new labels from the config file
        if 'ADDRESS_FIELD_SEPERATE' in cfg_dict:
            for new_label in cfg_dict['ADDRESS_FIELD_SEPERATE']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_start(self):

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
            for test_label in self.__checklabels:

                # Normalize and compare label
                if label.upper().replace(" ", "") == test_label:
                    note_fieldnames.append(label)
                    note_positions.append(pos)

        # If the list is not empty there is a seperate label error
        if note_fieldnames:
            # Concatenate the label list and produce a single error
            note = f"Fields labeled \"{', '.join(note_fieldnames)}\", should be merged into single \"Address\" labeled column"
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
        self.__checklabels = []

        # Append any new labels from the config file
        if 'MONETARY_FIELDS' in cfg_dict:
            for new_label in cfg_dict['MONETARY_FIELDS']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_row(self, row):
        # Regex to detect proper value
        check = re.compile(r"^-?\d+(\.\d{2})?$")

        # cell is a tuple of (field_name, cell value)
        for field, value in row.items():
            if field.upper() in self.__checklabels:

                # If strip() removes trail or lead whitespace get the error
                if not bool(check.match(str(value))):
                    note = "monetary values should only contain numbers to two decimal places, no '$' or commas"
                    yield MonetaryFields.from_row(
                        row, note=note, field_name=field
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
        self.__checklabels = []

        # Append any new labels from the config file
        if 'PHONE_NUMBER_FORMAT_ERROR' in cfg_dict:
            for new_label in cfg_dict['PHONE_NUMBER_FORMAT_ERROR']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_row(self, row):
        REQUIRED_CHARACTERS = 12
        # check if phone number is in header and get the key
        for label in self.resource.schema.field_names:
            if label.upper() in self.__checklabels:
                if row[label]:
                    phone_number_value = row[label]
                    phone_number_value_length = len(phone_number_value)
                    if not phone_number_value_length == REQUIRED_CHARACTERS:
                        note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                        yield PhoneNumberFormatError.from_row(
                            row, note=note, field_name=label
                        )
                    # regex search for phone number format 999-999-9999
                    # TODO Fix string casting
                    elif not re.search("^[0-9]{3}-[0-9]{3}-[0-9]{4}$", phone_number_value):
                        note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                        yield PhoneNumberFormatError.from_row(
                            row, note=note, field_name=label
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
        self.__checklabels = []

        # Append any new labels from the config file
        if 'WEB_LINK_FORMAT_ERROR' in cfg_dict:
            for new_label in cfg_dict['WEB_LINK_FORMAT_ERROR']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_row(self, row):
        for label in self.resource.schema.field_names:
            # if URL is a data field
            if label.upper() in self.__checklabels:
                URL_value = row[label]
                # regex search for URL format <a href="http://www.example.com">An example website</a>
                # Regex may allow multiple links
                if not re.search('^<a href="(http|https)://\S+">.*</a>$', URL_value):
                    note = f"Does not follow web link format. Web links must be written in HTML style, contain only one link, and begin with http:// or https://"
                    yield WebLinkFormatError.from_row(row, note=note, field_name=label)

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
        self.__checklabels = []

        # Append any new labels from the config file
        if 'GEOLOCATION_FORMAT_ERROR' in cfg_dict:
            for new_label in cfg_dict['GEOLOCATION_FORMAT_ERROR']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_start(self):
        # Gets the first valid keys from the config list
        POINT_KEY = next(filter(lambda label: "POINT" in label, self.__checklabels), None)
        LAT_KEY = next(filter(lambda label: "LAT" in label, self.__checklabels), None)
        LON_KEY = next(filter(lambda label: "LONG" in label, self.__checklabels), None)
        point_field = None
        lat_field = None
        lon_field = None
        config_error = False
        label_error = False
        
        # Check if config file has loaded the proper keys
        if bool((LAT_KEY and not LON_KEY) or (not LAT_KEY and LON_KEY)):
            config_error = True
        elif bool(not POINT_KEY and not LAT_KEY and not LON_KEY):
            config_error = True
        if config_error:
            note = f"Configuration does not follow GEOLOCATION_FORMAT_ERROR check. Must have a Point field and/or Latitude and longitude fields."
            yield errors.CheckError(note=note)

        # Check if both the lat and long fields exist in the file
        for field in self.resource.header.fields:
            if field['name'].upper() == POINT_KEY:
                point_field = field['name']
            if field['name'].upper() == LAT_KEY:
                lat_field = field['name']
            if field['name'].upper() == LON_KEY:
                lon_field = field['name']

        # Check if data file has both lat and long fields
        if bool((lat_field and not lon_field) or (not lat_field and lon_field)):
            label_error = True
        elif bool(not point_field and not lat_field and not lon_field):
            label_error = True
        if label_error:
            note = f"Data file does not follow geolocation format. Does not contain a Point field and/or Latitude and longitude fields."
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        # Gets the first valid keys from the config list
        POINT_KEY = next(filter(lambda label: "POINT" in label, self.__checklabels), None)
        LAT_KEY = next(filter(lambda label: "LAT" in label, self.__checklabels), None)
        LON_KEY = next(filter(lambda label: "LONG" in label, self.__checklabels), None)
        latitude_value = None
        longitude_value = None
        latitude = None
        longitude = None
        point = None

        # if latitude and longitude are data fields
        for label in self.resource.schema.field_names: 
            if LAT_KEY == label.upper():
                latitude_value = str(row[label])
                latitude_key = label
            elif LON_KEY == label.upper():
                longitude_value = str(row[label])
                longitude_key = label
            # if point is a data field
            elif POINT_KEY == label.upper():
                point_value = str(row[label])
                if not re.search("^POINT\(\-?[0-9]{1,3}\.[0-9]+ \-?[0-9]{1,2}\.[0-9]+\)$", point_value.upper()):
                    note = f"Does not follow geolocation format. Point field must be formatted the following way: POINT(longitude latitude)"
                    yield GeolocationFormatError.from_row(row, note=note, field_name=label)
                else:
                    point = point_value[6:-1]
                    point = point.split()
                    longitude_value = point[0]
                    latitude_value = point[1]
                    latitude_key = label
                    longitude_key = label
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
        self.__checklabels = []

        # Append any new labels from the config file
        if 'LOG_DATE_MATCH_ERROR' in cfg_dict:
            for new_label in cfg_dict['LOG_DATE_MATCH_ERROR']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_start(self):
        # Gets the first valid keys from the config list
        LOG_DATE_KEY = next(filter(lambda label: "LOG" in label, self.__checklabels), None)
        RECORD_DATE_KEY = next(filter(lambda label: "REC" in label, self.__checklabels), None)
        log_field = None
        rec_field = None
        
        # Check if config file has loaded the proper keys
        if bool((LOG_DATE_KEY and not RECORD_DATE_KEY) or (not LOG_DATE_KEY and RECORD_DATE_KEY)):
            note = f"Configuration does not follow LOG_DATE_MATCH_ERROR check. Must have a Log date and Record date field name to compare."
            yield errors.CheckError(note=note)

        # Check if both the lat and long fields exist in the file
        for field in self.resource.header.fields:
            if field['name'].upper() == LOG_DATE_KEY:
                log_field = field['name']
            if field['name'].upper() == RECORD_DATE_KEY:
                rec_field = field['name']

        # Check if data file has both lat and long fields
        if bool((log_field and not rec_field) or (not log_field and rec_field)) or bool(not log_field and not rec_field):
            note = f"Data file does not follow LOG_DATE_MATCH_ERROR format. Does not contain both a Log date and Record Date field."
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        LOG_DATE_KEY = next(filter(lambda label: "LOG" in label, self.__checklabels), None)
        RECORD_DATE_KEY = next(filter(lambda label: "REC" in label, self.__checklabels), None)
        log_field = None
        record_field = None
        for label in self.resource.schema.field_names:
            if label.upper() == LOG_DATE_KEY:
                log_field = label
            elif label.upper() == RECORD_DATE_KEY:
                record_field = label
        if str(row[log_field]) == str(row[record_field]):
            note = f"Does not follow log date standard. Log date must not match record date"
            yield LogDateMatchError.from_row(
                row, note=note, field_name=log_field
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
class valid_email_in_cell(Check):
    code = "valid-email-in-cell"
    Errors = [ValidEmailInCell]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__checklabels = []

        # Append any new labels from the config file
        if 'VALID_EMAIL_IN_CELL' in cfg_dict:
            for new_label in cfg_dict['VALID_EMAIL_IN_CELL']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_start(self):
        # Check if config file has loaded at least one keys
        if not self.__checklabels:
            note = f"Configuration does not follow VALID_EMAIL_IN_CELL check format. Must have at least one field name to check."
            yield errors.CheckError(note=note)


    def validate_row(self, row):
        for field, value in row.items():
            if field.upper() in self.__checklabels:
                # slicing domain name using slicing
                isError = False
                if str(value).find("@") == -1: # Find character "@" to check email format.
                    isError = True
                else:
                    domainName = value.split("@")[1]
                    # Regex to check valid
                    # domain name.
                    regex = "^((?!-)[A-Za-z0-9-]{1,63}(?<!-)\\.)[A-Za-z]{2,6}"
                    # Compile the ReGex
                    regexCompile = re.compile(regex)
                    if not re.search(regexCompile, domainName):
                        isError = True

                name = value.split(" ") # find space in email address.
                if len(name) > 1:
                    isError = True

                if isError: # If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: \"{value}\" is not an email"
                    yield ValidEmailInCell.from_row(
                        row, note=note, field_name=field
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Date format.
"""
class valid_date_in_cell(Check):
    code = "valid-date-in-cell"
    Errors = [ValidDateInCell]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__checklabels = []

        # Append any new labels from the config file
        if 'VALID_DATE_IN_CELL' in cfg_dict:
            for new_label in cfg_dict['VALID_DATE_IN_CELL']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())

    def validate_start(self):
        # Check if config file has loaded at least one keys
        if not self.__checklabels:
            note = f"Configuration does not follow VALID_DATE_IN_CELL check. Must add at least one field name to check."
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        for field, value in row.items():
            if field.upper() in self.__checklabels:
                isError = False
                try:  
                    date_time_obj = datetime.strptime(value, "%B %d, %Y") #try to parse this string value into date, if can not past. It mean this cell value is not true Date format
                except:
                    isError = True

                if isError:# If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: \"{value}\" is not a valid date"
                    yield ValidDateInCell.from_row(
                        row, note=note, field_name=field
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Negative Value format.
"""
class valid_negative_value_in_cell(Check):
    code = "valid-negative-value-in-cell"
    Errors = [ValidNegativeValueInCell]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__checklabels = []

        # Append any new labels from the config file
        if 'VALID_NEGATIVE_VALUE_IN_CELL' in cfg_dict:
            for new_label in cfg_dict['VALID_NEGATIVE_VALUE_IN_CELL']:
                if new_label.strip() not in self.__checklabels:
                    self.__checklabels.append(new_label.strip().upper())
    
    def validate_start(self):
        # Check if config file has loaded at least one keys
        if not self.__checklabels:
            note = f"Configuration does not follow VALID_NEGATIVE_VALUE_IN_CELL check. Must add at least one field name to check."
            yield errors.CheckError(note=note)

    def validate_row(self, row):
        for field, value in row.items():
            if field.upper() in self.__checklabels:
                isError = False
                if value.upper().find("MINUS") != -1: # find String contain String "MINUS" in cell
                    isError = True
                if (not isError) and (value.upper().find("SUB") != -1): # find String contain String "SUB" in cell
                    isError = True
                if (not isError) and (value.upper().find("MINU") != -1):# find String contain String "Minus" in cell
                    isError = True
                if (not isError) and (value.upper().find("(") != -1):# find String contain String "(" in cell
                    isError = True
                if isError:# If have error, we will set message into Note for Frictionless print into report
                    note = f"Type error in the cell value: \"{value}\" is not valid in Negative Value"
                    yield ValidNegativeValueInCell.from_row(
                        row, note=note, field_name=field
                    )

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check  Name Field format.
"""
class valid_namefield_value_in_cell(Check):
    code = "valid_namefield_value_in_cell"
    Errors = [ValidNamefieldValueInCell]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
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
                    note = f"Type error in the cell value: {cell} is not valid Name Field"
                    yield ValidNamefieldValueInCell.from_row(
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
class valid_address_value_in_cell(Check):
    code = "valid-address-value-in-cell"
    Errors = [ValidAddressValueInCell]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {}

    def validate_row(self, row):
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
                        f"Type error in the cell value: \"{cell}\", City State and zip codes should be separated out of the address and stored in separate columns named as CITY, STATE, and ZIPCODE"
                    )
                    yield ValidAddressValueInCell.from_row(
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
class valid_text_field_in_cell(Check):
    code = "valid-text-field-in-cell"
    Errors = [ValidTextFieldInCell]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

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
                    note = f"Type error in the cell value: {cell} is not a valid Text Field Value"
                    yield ValidTextFieldInCell.from_row(
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
class valid_data_completeness(Check):
    code = "valid-data-completeness"
    Errors = [ValidDataCompleteness]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        rowPosition = row.row_position
        for fieldPosition, field in enumerate(row):
            fieldName = str(row.field_names[fieldPosition])
            cell = str(row[fieldName])
            isError = False
            if isNotBlank(cell) == False: # run function to detect null value in cell
                isError = True
            if isError:# If have error, we will set message into Note for Frictionless print into report
                note = f"Error in the cell value: \"{cell}\" in row {rowPosition} is empty, It is not valid Data Completeness rule"
                yield ValidDataCompleteness.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

"""
This class to check Summerized Data format.
"""
class valid_summerized_data(Check):
    code = "valid-summerized-data"
    Errors = [ValidSummerizedData]

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
                note = f"Cell containing \"{cell}\" appears to summarize values from previous fields."
                yield ValidSummerizedData.from_row(row, note=note, field_name=fieldName)

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
