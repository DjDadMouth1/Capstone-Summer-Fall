from frictionless import Check, errors
import hashlib
from frictionless.errors import header
from custom_errors import *
import re

    
class numeric_field_error(Check):
    code = "numeric-field-error"
    Errors = [NumericFieldError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)

    def validate_row(self, row):
        text = ",".join(map(str, row.values()))
        hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        match = self.__memory.get(hash)
        if match:
            note = 'the same as row at position "%s"' % match
            yield errors.DuplicateRowError.from_row(row, note=note)
        self.__memory[hash] = row.row_position

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
class zip_code_format_error(Check):
    code = "zip-code-format-error"
    Errors = [ZipCodeFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.zip_code_keys = ['ZIP','ZIP CODE', 'ZIP CODES', 'ZIPCODE', 'ZIPCODES']
        self.actual_zip_code_key = None
        self.zip_code_length = None             
        
    # check if zip code is in header and get the key   
    def validate_start(self):
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names] 
        for zip_code_key in self.zip_code_keys:
            if zip_code_key in uppercase_headers:
                self.actual_zip_code_key = zip_code_key
        if not self.actual_zip_code_key:
                note = f"zip code format check requires a zip code field:{self.zip_code_keys}"
                yield errors.CheckError(note=note)
    
    def validate_row(self, row):
        zip_code_value = row[self.actual_zip_code_key]
        zip_code_value_length = len(zip_code_value)
        if zip_code_value_length != 5 and zip_code_value_length != 10:
            note = f"Does not follow ZIP code format. Only 5 digit and hyphenated 9 digit forms are acceptable"
            yield errors.ZipCodeFormatError.from_row(row, note=note, field_name=self.actual_zip_code_key)
        if zip_code_value_length == 5:
            if not zip_code_value.isdigit():
                note = f"Does not follow ZIP code format. Only 5 digit and hyphenated 9 digit values are acceptable"
                yield errors.ZipCodeFormatError.from_row(row, note=note, field_name=self.actual_zip_code_key)
        if zip_code_value_length == 10:
            first_five_digits = zip_code_value[:5]
            the_hyphen = zip_code_value[5]
            last_four_digits = zip_code_value[6:]
            first_five_digits = first_five_digits.isdigit()
            the_hyphen = the_hyphen == '-'
            last_four_digits = last_four_digits.isdigit()
            if not first_five_digits or not the_hyphen or not last_four_digits:
                note = f"Does not follow ZIP code format. Only 5 digit and hyphenated 9 digit values are acceptable"
                yield errors.ZipCodeFormatError.from_row(row, note=note, field_name=self.actual_zip_code_key)
                
    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
class zip_code_consistency_error(Check):
    code = "zip-code-consistency-error"
    Errors = [ZipCodeConsistencyError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
        self.zip_code_keys = ['ZIP','ZIP CODE', 'ZIP CODES', 'ZIPCODE', 'ZIPCODES']
        self.actual_zip_code_key = None
        self.zip_code_length = None             
        
    # check if zip code is in header and get the key   
    def validate_start(self):
        uppercase_headers = [label.upper() for label in self.resource.schema.field_names] 
        for zip_code_key in self.zip_code_keys:
            if zip_code_key in uppercase_headers:
                self.actual_zip_code_key = zip_code_key
        if not self.actual_zip_code_key:
                note = f"zip code consistency check requires a zip code field:{self.zip_code_keys}"
                yield errors.CheckError(note=note)
    
    def validate_row(self, row):
        zip_code_value = row[self.actual_zip_code_key]
        zip_code_value_length = len(zip_code_value)
        if self.zip_code_length is None:
            self.zip_code_length = zip_code_value_length
                
        elif zip_code_value_length != self.zip_code_length:
            note = f"Data in {self.actual_zip_code_key} column is inconsistent. Data does not match format in first row"
            yield errors.ZipCodeConsistencyError.from_row(row, note=note, field_name=self.actual_zip_code_key)

    # Metadata

    metadata_profile = {  # type: ignore
        "type": "object",
        "properties": {},
    }
class header_format_error(Check):
    code = "header-format-error"
    Errors = [HeaderFormatError]

    def __init__(self, descriptor=None):
        super().__init__(descriptor)
                 
    def validate_start(self):
        MAX_CHARACTERS = 30
        labels = self.resource.header.labels
        positions = self.resource.header.field_positions
        for field_name in self.resource.header.field_names:
            # if not a numeric character
            field_name_errors = []
            is_numeric = field_name.replace(".","").replace("-","").replace("_","").isalnum()
            is_uppercase = field_name.isupper()
            is_less_than_max_length = ( len(field_name) <= MAX_CHARACTERS )
            
            if not is_numeric:
                field_name_errors.append("not numeric, ")
            if not is_uppercase:
                field_name_errors.append("not uppercase,")
            if not is_less_than_max_length:
                field_name_errors.append("more than max 30 characters")
            field_name_errors = "".join(field_name_errors)
            print(field_name_errors)
            
            if not is_numeric or not is_uppercase or not is_less_than_max_length:
                # if it isnt uppercase or the length is greater than 30 characters
                    current_field_position = self.resource.header.field_names.index(field_name) + 1
                    note = field_name_errors
                    yield HeaderFormatError(labels=labels,row_positions=positions,note=note)
                    

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