from . import custom_checks
from frictionless import validate
import json

def custom_validate(file):
    checks = [custom_checks.numeric_field_error()]
    report = validate(file)
    with open('report.json','w') as outfile:
        json.dump(report.flatten(['message']),outfile, indent=2)

if __name__ == "__main__":
    custom_validate()