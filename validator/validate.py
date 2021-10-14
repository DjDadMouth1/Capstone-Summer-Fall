import json, csv, re
from frictionless import *
import custom_checks
"""
Portland State Capstone Team C - Open Data PDX
Validator basics
"""
"""
LEADING OR TRAILING SPACES

Opens the CSV and iterates through each row
then each field to check for leading and trailing spaces

r_count and f_count both add 1 assuming counting starts
at 1 not 0

Returns a list of the errors
"""
def leadTrailSpacesError(file):
    errorList = []
    with open(file, 'r') as f:
        data = csv.reader(f)
        for r_count, row in enumerate(data):
            for f_count, field in enumerate(row):
                temp = field.strip()
                if field != temp:
                    errorList.append(f'Value in row \"{r_count+1}\", position \"{f_count+1}\" has leading or trailing whitespace')
    return errorList

"""
DATA FILE FORMAT

Reads the file and assigns an error by row and field number
for values that are not double quoted

Returns a list of the errors
"""
def dataFileFormatError(file):
    errorList = []
    with open(file, 'r') as f:
        data = f.readlines()
        for r_count, row in enumerate(data):
            
            temp = re.split(',(?=([^\"]*\"[^\"]*\")*[^\"]*$)', row)
            if r_count == 0:
                print(row)
                print(len(temp))
                # for item in temp:
                #     print(item)
            
            
            # errorList.append(f'Value in row \"{r_count+1}\", position \"{f_count}\" is not double quoted')
       

    return errorList


"""
Saves the list of errors to report.json
"""
def saveJson(errorList):
    with open("report.json", "w") as f:
        json.dump(errorList, f, indent=4)

"""
TODO - Incorporate with the web portal to signal when the report is generated
for success or error
"""
if __name__ == "__main__":
    # TODO need to properly get the name from the web portal
    file = 'BDS - Permits issued Sample.csv'
    checks = [custom_checks.lead_trail_spaces]
    report = validate(file, checks=checks)
    saveJson(report)

