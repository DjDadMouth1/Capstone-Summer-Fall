from frictionless import Check, checks, validate, errors
import hashlib
from frictionless.errors import header, row
from sqlalchemy.sql.expression import false
from custom_errors import *
import re
from datetime import datetime
import regex

   
class header_format(Check):
    code = "header-format-error"
    Errors = [HeaderFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__errors = []
                 
    def validate_start(self):
        MAX_CHARACTERS = 30
  
        # Prepare context
        header_data = self.resource.header
        labels = header_data.labels
        fields = header_data.fields
        field_positions = header_data.field_positions
        
        # Iterate items
        field_number = 0
        for field_position, field, label in zip(field_positions, fields, labels):
        
            
            field_name_errors_note = []
            is_first_letter_alphabetic = label[0].isalpha()
            is_numeric = label.replace(".","").replace("-","").replace("_","").isalnum()
            is_uppercase = label.isupper()
            is_less_than_max_length = ( len(label) <= MAX_CHARACTERS )
            
            error_position_msg = f"The column name, '{label}', at field position {field_position} has the following error(s): "
            field_name_errors_note.append(error_position_msg)
            if not is_first_letter_alphabetic:
                field_name_errors_note.append("The first character is not alphabetic ")
            if not is_numeric:
                if len(field_name_errors_note) < 2:
                    field_name_errors_note.append("It contains non-alphanumeric character(s) ")
                else:
                    field_name_errors_note.append(", it contains non-numeric character(s) ")
            if not is_uppercase:
                if len(field_name_errors_note) < 2:
                    field_name_errors_note.append("It contains lowercase character(s)")
                else:
                    field_name_errors_note.append(", it contains lowercase character(s)")
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
            field_name_errors_note = "".join( field_name_errors_note )
            
    
            # column name does not meet format standards
            if not is_numeric or not is_uppercase or not is_less_than_max_length or not is_first_letter_alphabetic:
                yield HeaderFormatError( note=field_name_errors_note )
                
    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
    

class numeric_field(Check):
    code = "numeric-field-error"
    Errors = [NumericFieldError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)


    # check if there is are numberic fields with barnumbers.
    def validate_start(self):
        column_with_numbers = [field for field in self.resource.schema.fields if (field["type"] == "number" or field["type"] == "integer")] 
        if not column_with_numbers:
            note = f"Boolean format consistency check requires a number data type column. Ignore this message if the data does not contain columns containing numbers. Note that if a field contains a non-numeric character, the number in the field it will be saved as a string (e.g. 90% and $1.50 will both saved as strings rather than numbers.)"
            yield errors.CheckError(note=note)
            

    def validate_row(self, row):
        column_with_numbers = [field["name"] for field in self.resource.schema.fields if (field["type"] == "number" or field["type"] == "integer")]
        for field_name, field_value in zip(row.field_names, row.cells):
            if field_name in column_with_numbers:
                field_value_string = str(field_value)
                
                # check if it contains any non-numeric characters (looking for %,$, etc.)
                if not field_value_string.replace(".","").replace("-","").isalnum():    
                    note = f"Data in {field_name} column contains special characters. All characters in a column designated a numeric must be numberic. Remove the non-numeric characters from the following value: {field_value_string}."
                    yield NumericFieldError.from_row(row, note=note, field_name=field_name) 
                
    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
    

class zip_code_format(Check):
    code = "zip-code-consistency-error"
    Errors = [ZipCodeFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
          
        
    # check if zip code is in header and get the key   
    def validate_start(self):
        ZIP_CODE_KEYS = ['ZIP','ZIP CODE', 'ZIP CODES', 'ZIPCODE', 'ZIPCODES']
        actual_zip_code_key = None
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names] 
        for zip_code_key in ZIP_CODE_KEYS:
            if zip_code_key in uppercase_headers:
                actual_zip_code_key = zip_code_key
        if not actual_zip_code_key:
                note = f"zip code format check requires a zip code field:{ZIP_CODE_KEYS}"
                yield errors.CheckError(note=note)
    
    def validate_row(self, row):
        print("in row")
        for field_name, cell in row.items():
            ZIP_CODE_KEYS = ['ZIP','ZIP CODE', 'ZIP CODES', 'ZIPCODE', 'ZIPCODES']
            if field_name.upper() in ZIP_CODE_KEYS:
                zip_code_value = str(cell)
                if not re.search("^[0-9]{5}-[0-9]{4}$", zip_code_value) and not re.search("^[0-9]{5}$", zip_code_value):
                    note = f"Does not follow ZIP code format. Only 5 digit and hyphenated 9 digit forms are acceptable (for example 97217 or 97217-1202)"
                    yield ZipCodeFormatError.from_row(row, note=note, field_name=field_name)
             
    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class zip_code_consistency(Check):
    code = "zip-code-consistency-error"
    Errors = [ZipCodeFormatConsistencyError]
    
    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {} 
     
    # check if zip code is in header and get the key   
    def validate_start(self):
        ZIP_CODE_KEYS = ['ZIP','ZIP CODE', 'ZIP CODES', 'ZIPCODE', 'ZIPCODES']
        has_zip_code = False
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names] 
        for zip_code_key in ZIP_CODE_KEYS:
            if zip_code_key in uppercase_headers:
                has_zip_code = True
        if not has_zip_code:
                note = f"Zip Code consistency check requires one of the following fields to exist:{ZIP_CODE_KEYS} Ignore this message if data does not contain zip codes."
                yield errors.CheckError(note=note)             
        
    def validate_row(self, row):
        ZIP_CODE_KEYS = ['ZIP','ZIP CODE', 'ZIP CODES', 'ZIPCODE', 'ZIPCODES']
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names] 
        for field_name, cell in row.items():
            if field_name.upper() in ZIP_CODE_KEYS:
                zip_code_value = str(cell)
                zip_code_length = len(str(cell))
                match = self.__memory.get(field_name)
                
                # field format not saved yet
                if not match:                      
                    if not re.search("^[0-9]{5}-[0-9]{4}$", zip_code_value) and not re.search("^[0-9]{5}$", zip_code_value):
                        note = f"Does not follow ZIP code format. Only 5 digit and hyphenated 9 digit forms are acceptable (for example 97217 or 97217-1202)"
                        yield ZipCodeFormatError.from_row(row, note=note, field_name=field_name)
                    else:
                        self.__memory[field_name] = (zip_code_length, row.row_position)
                    
                if match:
                    saved_length = match[0]
                    if zip_code_length != saved_length:
                        note = f"Data in {field_name} column is inconsistent. Data does not match format at row posistion {match[1]}"
                        yield ZipCodeFormatConsistencyError.from_row(row, note=note, field_name=field_name)      
                
    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
class phone_number_format_error(Check):
    code = "phone-number-format-error"
    Errors = [PhoneNumberFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        REQUIRED_CHARACTERS = 12
        PHONE_NUMBER_KEYS = ['PHONE','PHONE NUMBER', 'PHONE NUMBERS', 'PHONENUMBER', 'PHONENUMBERS']
        actual_phone_number_key = None
        # check if phone number is in header and get the key
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names]
        for phone_number_key in PHONE_NUMBER_KEYS:
            if phone_number_key in uppercase_headers:
                actual_phone_number_key = phone_number_key
        if actual_phone_number_key:
            phone_number_value = row[actual_phone_number_key]
            phone_number_value_length = len(phone_number_value)
            if not phone_number_value_length == REQUIRED_CHARACTERS:
                note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                yield PhoneNumberFormatError.from_row(row, note=note, field_name=actual_phone_number_key)
            # regex search for phone number format 999-999-9999
            elif not re.search("^[0-9]{3}-[0-9]{3}-[0-9]{4}$", phone_number_value):
                note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                yield PhoneNumberFormatError.from_row(row, note=note, field_name=actual_phone_number_key)

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

class boolean_format_consistency(Check):
    code = "boolean-format-consistency-error"
    Errors = [BooleanFormatConsistencyError]
    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.__memory = {} 
          
        
    # check if there is are boolean   
    def validate_start(self):
        column_data_types = [field["type"] for field in self.resource.schema.fields] 
        if 'boolean' not in column_data_types:
            note = f"Boolean format consistency check requires a boolean data type column. Ignore this message if the data does not contain boolean columns (True/False)."
            yield errors.CheckError(note=note)

    
    def validate_row(self, row):
        boolean_sets = [{"1","0"}, {"t", "f"}, {"true", "false"}, {"yes", "no"}, {"y", "n"}, {"on", "off"}]
        column_data_types = [field["name"] for field in self.resource.schema.fields if field["type"] == "boolean"] 
                          
        for field_name, field_value in zip(row.field_names, row.cells):
            if field_name in column_data_types:
                field_value_string = str(field_value)
                saved_boolean_format = self.__memory.get(field_name)
                
                # field boolean format not saved yet
                if not saved_boolean_format: 
                        for boolean_set in boolean_sets:
                            if field_value_string in boolean_set:                     
                                self.__memory[field_name] = (boolean_set, row.row_position)    
                if saved_boolean_format:
                    current_boolean_set = saved_boolean_format[0]
                    if field_value_string not in current_boolean_set:
                        note = f"Boolean data in {field_name} column is not consistent with other boolean values in the column. The current value is {field_value_string} and must be updated ot be one of the following:{current_boolean_set}, which was decided at the follwing row: {saved_boolean_format[1]}."
                        yield BooleanFormatConsistencyError.from_row(row, note=note, field_name=field_name) 
                


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

    def validate_row(self, row):

        # cell is a tuple of (field_name, cell value)
        for cell in row.items():
            if not isinstance(cell[1], str):
                continue

            # If strip() removes trail or lead whitespace get the error
            if cell[1] != cell[1].strip():
                note = "value has leading or trailing whitespace"
                yield LeadTrailWhitespace.from_row(
                    row, note=note, field_name=cell[0]
                )

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


class address_field_seperate(Check):
    """
    ADDRESS

    Checks for address labels that are seperated to multiple columns by
    Number, Street, Quadrant instead of a single Address field

    """
    code = "address-field-seperated"
    Errors = [AddressFieldSeperated]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)


    def validate_start(self):
        address_labels = ["STREETNUMBER", "STREET", "QUADRANT"]
        note_fieldnames = []
        note_positions = []

        # Loop through labels and label positions
        for label, pos in zip(self.resource.header.labels, self.resource.header.field_positions):
            # Skip blanks
            if label is None:
                continue
            print(label)

            # Compate each label to all possible seperate address labels
            for test_label in address_labels:

                # Normalize and compare label
                if label.upper().replace(" ", "") == test_label:
                    note_fieldnames.append(label)
                    note_positions.append(pos)

        # If the list is not empty there is a seperate label error
        if note_fieldnames:
            # Concatenate the label list and produce a single error
            note = f"Fields labeled \"{', '.join(note_fieldnames)}\", should be merged into single \"Address\" label column"
            yield AddressFieldSeperated(labels=note_fieldnames, row_positions=note_positions, note=note)

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
        Monetary_Labels = ['COST','PRICE','VALUATION']
        check = re.compile(r'^\d+(\.\d{2})?$')
        
        # cell is a tuple of (field_name, cell value)
        for cell in row.items():
            print(str(cell[1]) + ' type is ' + str(type(cell[1])))
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
class phone_number_format_error(Check):
    code = "phone-number-format-error"
    Errors = [PhoneNumberFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        REQUIRED_CHARACTERS = 12
        PHONE_NUMBER_KEYS = ['PHONE','PHONE NUMBER', 'PHONE NUMBERS', 'PHONENUMBER', 'PHONENUMBERS']
        actual_phone_number_key = None
        # check if phone number is in header and get the key
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names]
        for phone_number_key in PHONE_NUMBER_KEYS:
            if phone_number_key in uppercase_headers:
                actual_phone_number_key = phone_number_key
        # if key is found, check the rows
        if actual_phone_number_key:
            phone_number_value = row[actual_phone_number_key]
            phone_number_value_length = len(phone_number_value)
            if not phone_number_value_length == REQUIRED_CHARACTERS:
                note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                yield PhoneNumberFormatError.from_row(row, note=note, field_name=actual_phone_number_key)
            # regex search for phone number format 999-999-9999
            elif not re.search("^[0-9]{3}-[0-9]{3}-[0-9]{4}$", phone_number_value):
                note = f"Does not follow phone number format. Only ten-digit numbers separated by hyphens (-) are acceptable"
                yield PhoneNumberFormatError.from_row(row, note=note, field_name=actual_phone_number_key)

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
        URL_KEY = 'URL'
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names]
        # if URL is a data field
        if URL_KEY in uppercase_headers:
            URL_value = row[URL_KEY]
            # regex search for URL format <a href="http://www.example.com">An example website</a>
            if not re.search("^<a href=\"(http|https)://\S+\">.*</a>$", URL_value):
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
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names]
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
            point = point_value[6:-1]
            point = point.split()
            if not len(point) == 2:
                note = f"Does not follow geolocation format. Point must be formatted the following way: POINT(longitude latitude)"
                yield GeolocationFormatError.from_row(row, note=note, field_name=POINT_KEY)
            else:
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
                yield GeolocationFormatError.from_row(row, note=note, field_name=latitude_key)
            elif not re.search("^\-?[0-9]{1,3}\.[0-9]+$", longitude_value):
                note = f"Does not follow geolocation format. Longitude must be a decimal number"
                yield GeolocationFormatError.from_row(row, note=note, field_name=longitude_key)
            else:
                latitude = float(latitude_value)
                longitude = float(longitude_value)
                if latitude > 90.0 or latitude < -90.0:
                    note = f"Out of bounds. Latitude must be between 90 and -90 degrees"
                    yield GeolocationFormatError.from_row(row, note=note, field_name=latitude_key)
                if longitude > 180.0 or longitude < -180.0:
                    note = f"Out of bounds. Longitude must be between 180 and -180 degrees"
                    yield GeolocationFormatError.from_row(row, note=note, field_name=longitude_key)
        
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
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names]
        if LOG_DATE_KEY in uppercase_headers and RECORD_DATE_KEY in uppercase_headers:
            if str(row[LOG_DATE_KEY]) == str(row[RECORD_DATE_KEY]):
                note = f"Does not follow log date standard. Log date must not match record date"
                yield LogDateMatchError.from_row(row, note=note, field_name=LOG_DATE_KEY)
    
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
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names]
        # Don't repeat yourself. There should be a function for this, but Frictionless is weird so I was afraid to try
        if BUREAU_CODE_KEY in uppercase_headers and BUREAU_DESCRIPTION_KEY in uppercase_headers:
            if not str(row[BUREAU_CODE_KEY]) in BUREAU_CODES:
                note = f"Does not follow bureau code standard. Bureau code not found"
                yield BureauCodeMatchError.from_row(row, note=note, field_name=BUREAU_CODE_KEY)
            elif not str(row[BUREAU_DESCRIPTION_KEY]) in BUREAU_CODES.values():
                note = f"Does not follow bureau code standard. Bureau description not found"
                yield BureauCodeMatchError.from_row(row, note=note, field_name=BUREAU_DESCRIPTION_KEY)
            elif not BUREAU_CODES[str(row[BUREAU_CODE_KEY])] == row[str(BUREAU_DESCRIPTION_KEY)]:
                note = f"Does not follow bureau code standard. Bureau code must match bureau description"
                yield BureauCodeMatchError.from_row(row, note=note, field_name=BUREAU_CODE_KEY)
        elif BUREAU_CODE_KEY in uppercase_headers:
            if not str(row[BUREAU_CODE_KEY]) in BUREAU_CODES:
                note = f"Does not follow bureau code standard. Bureau code not found"
                yield BureauCodeMatchError.from_row(row, note=note, field_name=BUREAU_CODE_KEY)
        elif BUREAU_DESCRIPTION_KEY in uppercase_headers:
            if not str(row[BUREAU_DESCRIPTION_KEY]) in BUREAU_CODES.values():
                note = f"Does not follow bureau code standard. Bureau description not found"
                yield BureauCodeMatchError.from_row(row, note=note, field_name=BUREAU_DESCRIPTION_KEY)

        
    # Metadata
    
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
   
   # Faihan's SECTION 
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
            if (fieldName.upper().find("EMAIL") != -1):  # only run on field name is email
                cell = str(row[fieldName])
                # slicing domain name using slicing
                isError = False
                if (str(cell).find("@") == -1):
                    isError = True
                else:
                    domainName = cell.split('@')[1]
                    # Regex to check valid
                    # domain name.
                    regex = "^((?!-)[A-Za-z0-9-]{1,63}(?<!-)\\.)[A-Za-z]{2,6}"
                    # Compile the ReGex
                    regexCompile = re.compile(regex)
                    if (not re.search(regexCompile, domainName)):
                        isError = True

                name = cell.split(" ")
                if len(name) > 1:
                    isError = True

                if isError:
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not an email"
                    yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


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
            if (fieldName.upper().find("DATE") != -1):  # only run on field name is date
                cell = str(row[fieldName])
                isError = False
                try:
                    date_time_obj = datetime.strptime(cell, '%d/%m/%y')
                except:
                    isError = True

                if isError:
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid date"
                    yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


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
            if (fieldName.upper().find("AMOUNT") != -1) or (fieldName.upper().find("VALUE") != -1) \
                    or (fieldName.upper().find("AMT") != -1) or (fieldName.upper().find("SALARY") != -1):
                cell = str(row[fieldName])
                isError = False
                if cell.upper().find("MINUS") != -1:
                    isError = True
                if (not isError) and (cell.upper().find("MINUS") != -1):
                    isError = True
                if (not isError) and (cell.upper().find("MINU") != -1):
                    isError = True
                if (not isError) and (cell[0].upper().find("(") != -1):
                    isError = True
                if isError:
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid in Negative Value"
                    yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


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
            if (fieldName.upper().find("NAME") != -1):
                cell = str(row[fieldName])
                # Split the string and get all words in a list
                list_of_words = cell.split()
                isError = False
                for elem in list_of_words:
                    # capitalize first letter of each word and add to a string
                    tmp = elem.strip().capitalize()
                    if (tmp != elem):
                        isError = True
                if isError:
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid Name Field"
                    yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


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
            if (fieldName.upper().find("ADDRESS") != -1) or (fieldName.upper().find("STATE") != -1) \
                    or (fieldName.upper().find("ZIP") != -1) or (fieldName.upper().find("CITY") != -1):
                cell = str(row[fieldName])
                isError = False
                if cell.upper().find(",") != -1:  # 'find comma to detect error
                    isError = True
                if isError:
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: " \
                           f"City State and zip codes should be separated out of the address and stored in separate columns named as CITY, STATE, and ZIPCODE"
                    yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


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
            if (fieldName.upper().find("AMOUNT") == -1) or (fieldName.upper().find("VALUE") == -1) \
                    or (fieldName.upper().find("AMT") == -1) or (
                    fieldName.upper().find("SALARY") == -1):  # ignore number fields
                cell = str(row[fieldName])
                isError = False
                if re.search('<[^/>][^>]*>', cell) != None:
                    isError = True
                if isError:
                    note = f"Type error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is not valid in Text Field Value"
                    yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


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
            if (isNotBlank(cell) == False):
                isError = True
            if isError:
                note = f"Error in the cell value: {cell} in row {rowPosition} and field {fieldName} at position {fieldPosition}: Is empty, It is not valid Data Completeness rule"
                yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }

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
            if (cell.upper().find("TOT") >= 0) or (cell.upper().find("SUM") >= 0):
                isError = True
            if isError:
                note = f"Row {rowPosition}: Is including roll-ups, subtotal and total of values in cells as part of the column. It is not valid Summarized Data, applications can compute these values and have totals of subtotals skews results"
                yield errors.CellError.from_row(row, note=note, field_name=fieldName)

    # Metadata
    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }


def isNotBlank(myString):
    if myString and myString.strip():
        # myString is not None AND myString is not empty or blank
        return True
    # myString is None OR myString is empty or blank
    return False
