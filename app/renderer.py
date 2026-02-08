def render_table(fields):
    table = []

    for f in fields:
        table.append({
            "Row": f.row,
            "Label": f.label,
            "Amount": f.value
        })

    return table