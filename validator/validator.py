from . import custom_checks
from frictionless import describe, validate
import json

def custom_validate(file, output_selection = None):
    output_report = None
    new_checks = [custom_checks.monetary_fields()]
    report = validate(file, checks=new_checks)
    
    if output_selection == 'schema':
        output_report = describe(file)
    elif output_selection == 'error':
        output_report = report.flatten(['message'])
    else:
        output_report = report

    with open('report.json','w') as outfile:
        json.dump(output_report,outfile, indent=2)
    
    return 

if __name__ == "__main__":
    custom_validate()