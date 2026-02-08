def validate_fields(fields):
    errors = []

    for field in fields:
        if field.row == "030" and field.value > 0:
            errors.append("Row 030 (CET1 deductions) must be negative.")

    return errors

def validate_total(fields):
    values = {f.row: f.value for f in fields}

    if "050" in values:
        calculated = (
            values.get("010", 0) +
            values.get("020", 0) +
            values.get("030", 0) +
            values.get("040", 0)
        )

        if values["050"] != calculated:
            return ["Total Own Funds mismatch."]
    
    return []