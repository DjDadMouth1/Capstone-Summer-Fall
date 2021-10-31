from validator import custom_checks
from frictionless import validate
import json

def custom_validate(filename):
    checks = [custom_checks.numeric_field_error()]
    report = validate(filename, checks)
    with open('report.txt','w') as outfile:
        json.dump(report.flatten(['message']),outfile)