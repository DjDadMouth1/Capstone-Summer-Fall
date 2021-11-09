from . import custom_checks
from frictionless import validate
import json

def custom_validate(file):
    new_checks = [custom_checks.numeric_field()]
    report = validate(file, checks=new_checks)
    with open('report.json','w') as outfile:
        json.dump(report.flatten(),outfile, indent=2)
    
    return 

if __name__ == "__main__":
    custom_validate()