from typing import ValuesView
from frictionless import validate
from pprint import pprint

if __name__ == "__main__":
    report = validate('invalid.csv')
    pprint(report.flatten(['message']))