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

# # Example usage
# html_output = html_tt(["011X11X01X11X001", "0101101001011010", "0111110000011001"], ["A", "B", "C", "D", "F", "G", "RESULT"])
# print(html_output)
# html_output2 = html_tt(["00X1", "11x0", "0X10"], ["F", "G", "RES1", "RES2,", "RES3"])
# print(html_output2)
# with open("output2.html", "w") as file:
#     file.write(html_output)
#     file.write(html_output2)
