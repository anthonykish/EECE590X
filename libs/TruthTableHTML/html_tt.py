## html_tt (s, col_headers)
# Parameter 1 - Either a string or a list of strings where each string
#   contains the data for your truth table output. Strings must contain
#   only '0', '1', and 'x' or 'X' for "don't cares". Each string must
#   be of equal length, and said length should be an appropriate power
#   of 2.
# Parameter 2 - A list of strings containing the column labels for each
#   input and output in your truth table. The list must have the
#   appropriate amount of headers to label each column.
# Return Value - Function returns a string containing the entire html
#   truth table

def html_tt(s, col_headers):
    import math
    if type(s) == str:
        slist = list()
        slist.append(s)
    else:
        slist = s
    
    # Parameter Filtering
    num_inputs = 0
    for s in slist:
        match_check = num_inputs
        num_inputs = int(math.log2(len(s)))
        if s == slist[0]:
            continue
        if match_check != num_inputs:
            return "ERROR - Inconsistent result length"
        
    # Table dimensions (Without Labels)
    rows, cols = 2**num_inputs, num_inputs+len(slist)
    
    if len(slist[0]) != rows:
        return "ERROR - Invalid data string length. Make sure the " \
            "amount of data strign characters is a power of 2."
        
    for s in slist:
        for char in s:
            if char != '0' and char != '1' and char != 'X' and char != 'x':
                return "ERROR - data string contains invalid character. "\
                    "Make sure the string contains only '0', '1', 'x' or 'X'"
        
    if len(col_headers) != num_inputs+len(slist):
        return "ERROR - Invalid quantitiy of column headers given. " \
            "Make sure the list contains a string for each input and result"
        
    # Generating input data
    in_data = []
    swap = rows
    for col in range(num_inputs):
        sublist = []
        swap = swap/2
        flag = 1
        for i in range(rows):
            if i%swap==0:
                flag ^= 1
            sublist.append(f"{flag}")
        in_data.append(sublist)
    
    # Table declaration and adding the column labels
    table = "<table style='border-collapse: collapse; text-align: " \
        "center'><tr>"
    for label in col_headers:
        table += f"    <th style='border-bottom: 2px solid black; " \
            f"padding: 15px;'>{label}</th>"
    table += "</tr>"
    
    # Filling in the table
    for r in range(rows):
        
        # Filling inputs
        table += "  <tr>"
        for col in in_data:
            table += f"    <td>{col[r]}</td>"

        # Filling outputs
        for s in slist:
            index = r
            char = s[index] if index < len(s) else "&nbsp;"
            if s == slist[0]: 
                table += f"    <td style='border-left: 2px solid " \
                    f"black;'>{char}</td>"
            else:
                table += f"    <td>{char}</td>"
        table += "</tr>"

    table += "</table>"
    return table

def html_st(next_states, outputs, input_headers=None, state_names=None):
    """
    Build an HTML state table.

    Parameters
    ----------
    next_states : list[list[str]]
        2D list where each row corresponds to one present state and each
        column corresponds to one input condition.
        Example:
            [
                ["S3", "S2"],   # row for S0: a=0 -> S3, a=1 -> S2
                ["S1", "S0"],   # row for S1
                ["S3", "S2"],   # row for S2
                ["S1", "S0"]    # row for S3
            ]

    outputs : list[str]
        Output value for each state row.
        Example:
            ["00", "01", "11", "10"]

    input_headers : list[str], optional
        Labels for each input column under the "Next State" section.
        Example:
            ["a=0", "a=1"]
        If None, defaults to ["Input 0", "Input 1", ...].

    state_names : list[str], optional
        Labels for each state row.
        Example:
            ["S0", "S1", "S2", "S3"]
        If None, defaults to ["S0", "S1", "S2", ...].

    Returns
    -------
    str
        HTML string for the full state table.

    Example
    -------
    next_states = [
        ["S3", "S2"],
        ["S1", "S0"],
        ["S3", "S2"],
        ["S1", "S0"]
    ]

    outputs = ["00", "01", "11", "10"]

    html = html_st(
        next_states,
        outputs,
        input_headers=["a=0", "a=1"],
        state_names=["S0", "S1", "S2", "S3"]
    )
    """
    # Basic parameter checks
    if not isinstance(next_states, list) or len(next_states) == 0:
        return "ERROR - next_states must be a non-empty 2D list"

    if not isinstance(outputs, list) or len(outputs) != len(next_states):
        return "ERROR - outputs must be a list with one entry per state row"

    num_states = len(next_states)
    num_inputs = len(next_states[0])

    if num_inputs == 0:
        return "ERROR - each next_states row must contain at least one next-state entry"

    for row in next_states:
        if not isinstance(row, list):
            return "ERROR - next_states must be a 2D list"
        if len(row) != num_inputs:
            return "ERROR - inconsistent number of next-state columns"

    # Default row labels
    if state_names is None:
        state_names = [f"S{i}" for i in range(num_states)]
    if len(state_names) != num_states:
        return "ERROR - state_names must contain one name per state row"

    # Default input labels
    if input_headers is None:
        input_headers = [f"Input {i}" for i in range(num_inputs)]
    if len(input_headers) != num_inputs:
        return "ERROR - input_headers must match number of next-state columns"

    # Build table
    table = "<table style='border-collapse: collapse; text-align: center;'>"

    # Top header row
    table += (
        "<tr>"
        "  <th rowspan='2' style='border-bottom: 2px solid black; padding: 15px;'>State</th>"
        f"  <th colspan='{num_inputs}' style='border-left: 2px solid black; "
        "border-bottom: 2px solid black; padding: 15px;'>Next State</th>"
        "  <th rowspan='2' style='border-left: 2px solid black; border-bottom: 2px solid black; "
        "padding: 15px;'>Output</th>"
        "</tr>"
    )

    # Second header row
    table += "<tr>"
    for i, label in enumerate(input_headers):
        if i == 0:
            table += (
                f"  <th style='border-left: 2px solid black; border-bottom: 2px solid black; "
                f"padding: 10px;'>{label}</th>"
            )
        else:
            table += f"  <th style='border-bottom: 2px solid black; padding: 10px;'>{label}</th>"
    table += "</tr>"

    # Data rows
    for r in range(num_states):
        table += "<tr>"
        table += f"  <td style='padding: 12px;'>{state_names[r]}</td>"

        for c in range(num_inputs):
            if c == 0:
                table += (
                    f"  <td style='border-left: 2px solid black; padding: 12px;'>"
                    f"{next_states[r][c]}</td>"
                )
            else:
                table += f"  <td style='padding: 12px;'>{next_states[r][c]}</td>"

        table += (
            f"  <td style='border-left: 2px solid black; padding: 12px;'>"
            f"{outputs[r]}</td>"
        )
        table += "</tr>"

    table += "</table>"
    return table

# # Example usage
# html_output = html_tt(["011X11X01X11X001", "0101101001011010", "0111110000011001"], ["A", "B", "C", "D", "F", "G", "RESULT"])
# print(html_output)
# html_output2 = html_tt(["00X1", "11x0", "0X10"], ["F", "G", "RES1", "RES2,", "RES3"])
# print(html_output2)
# with open("output2.html", "w") as file:
#     file.write(html_output)
#     file.write(html_output2)
