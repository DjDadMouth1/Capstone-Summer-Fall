import json, csv
from frictionless import *
"""
Portland State Capstone Team C - Open Data PDX
Validator basics
"""


"""
Runs the default Frictionless validation
and compiles just the list of errors from the report

Returns a list of the errors
"""
def baseFrictionless(file):
    # Run baseline frictionless validation checks
    report = validate(file)

    # Capture a list of just the error messages
    errorList = []
    for msg in report.flatten(["message"]):
        errorList.append(msg[0])

    return errorList

"""
Opens the CSV and iterates through each row
then each field to check for leading and trailing spaces

r_count and f_count both add 1 assuming counting starts
at 1 not 0

Returns a list of the errors
"""
def leadTrailSpaces(file):
    errorList = []
    with open(file, 'r') as f:
        data = csv.reader(f)
        for r_count, row in enumerate(data):
            for f_count, field in enumerate(row):
                temp = field.strip()
                if field != temp:
                    errorList.append(f'Value in the field at row \"{r_count+1}\", position \"{f_count+1}\" has leading or trailing whitespace')
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
    file = "BDS - Permits issued Sample.csv"
    errorList = baseFrictionless(file)
    errorList += leadTrailSpaces(file)
    saveJson(errorList)

