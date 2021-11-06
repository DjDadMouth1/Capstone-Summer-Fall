from frictionless import Check, errors
import hashlib
from frictionless.errors import header
from custom_errors import *

    
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