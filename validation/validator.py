from re import S
from . import custom_checks
from frictionless import describe, validate
import json, importlib, inspect
import importlib.resources as resources

# Load the checks.cfg file into a dictionary with
# the User's custom fields


def custom_validate(file, output_selection = None):
    check_selection = check_select()
    output_report = None
    
    report = validate(file, checks=check_selection)
    
    if output_selection == 'schema':
        output_report = describe(file)
    elif output_selection == 'error':
        output_report = report.flatten(['note','message','description'])
    else:
        output_report = report

    with open('./userfiles/report.json','w') as outfile:
        json.dump(output_report,outfile, indent=2)
    
    return

def check_select():
    add_checks = []
    check_file = resources.open_text('settings', 'checks.cfg')
    for line in check_file:
        custom_check, value = line.rstrip('\n').split('=')
        if value.strip() == '1':
            add_checks.append(custom_check.strip())

    print(add_checks)

    selected_checks = []
    for name, obj in inspect.getmembers(custom_checks):
        if inspect.isclass(obj):
            if name in add_checks:
                selected_checks.append(obj())

    return selected_checks
    
    