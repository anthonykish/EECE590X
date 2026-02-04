def html_table(headers, cols):
    
    """
    Makes an HTML table as a string
    headers: list of strings
    cols: list of lists of strings (must be same length)
    Returns a string
    """

    # Table declaration and adding the column labels
    table = "<table style='border-collapse: collapse; text-align: " \
        "center'><tr>"
    for label in headers:
        table += f"    <th style='border-bottom: 2px solid black; " \
            f"padding: 15px;'>{label}</th>"
    table += "</tr>"

    # Filling in the table
    for i in range(len(cols[1])):
        table += "<tr>"
        for col in cols:
            item = col[i]
            table += f"<td>{item}</td>"
        table += "</tr>"
    
    # Footer
    table += "</table>"

    return table


# I'm kinda silly and didn't think to make these until the end of the semester

def italic(s):
    return f"<i>{s}</i>"

def bold(s):
    return f"<b>{s}</b>"

def code(s):
    return f"<code>{s}</code>"

def underline(s):
    return f"<ins>{s}</ins>"

def subscript(s):
    return f"<sub>{s}</sub>"

def superscript(s):
    return f"<sup>{s}</sup>"

def strike(s):
    return f"<del>{s}</del>"

def highlight(s):
    return f"<mark>{s}</mark>"

def emphasize(s):
    return f"<em>{s}</em>"

