from re import S
from . import custom_checks
from frictionless import describe, validate
import json, inspect
import importlib.resources as resources

# Load the checks.cfg file into a dictionary with
# the User's custom fields


def custom_validate(file, output_selection = None):
    check_selection = check_select()
    output_report = None
    
    filepath = './static/userfiles/' + file

    print(filepath)

    report = validate(filepath, checks=check_selection)
    
    if output_selection == 'schema':
        output_report = describe(filepath)
    elif output_selection == 'error':
        output_report = report.flatten(['note','message','description'])
    else:
        output_report = report
    
    print(output_selection)
    if output_selection != '':
        output_selection = '-' + output_selection

    new_file = './static/userfiles/' + file.split('.')[0] + output_selection + '-report.json'
    
    with open(new_file,'w') as outfile:
        json.dump(output_report,outfile, indent=2)
    
    return new_file.split('./',1)[1]

def check_select():
    add_checks = []
    check_file = resources.open_text('settings', 'checks.cfg')
    for line in check_file:
        custom_check, value = line.rstrip('\n').split('=')
        if value.strip() == '1':
            add_checks.append(custom_check.strip())

    selected_checks = []
    for name, obj in inspect.getmembers(custom_checks):
        if inspect.isclass(obj):
            if name in add_checks:
                selected_checks.append(obj())

    return selected_checks
    
    