from frictionless import errors

class LeadTrailWhitespace(errors.ConstraintError):
    code = "leading-or-trailing-whitespace"
    name = "Leading or Trailing Whitespace"
    tags = ["#table", "#row", "#cell"]
    template = "The cell {cell} in row at position {rowPosition} at position {fieldPosition} does not conform to a constraint: {note}"
    description = "The field value contains leading or trailing whitespace"