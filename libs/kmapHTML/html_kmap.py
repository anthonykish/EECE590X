## html_kmap (s)
# Parameter 1 - A string that contains the data to fill in the kmap
#   with. Strings must contain only '0', '1', and 'x'/'X' to represent
#   "don't cares". String length should be an appropriate power of 2. 
#   The bit string should be raw, with bits listed in truth table order
# Return Value - Function returns a string containing the entire html
#   kmap
import math

def generate_gray_code(n):
    #Generates a list of n-bit Gray code sequences.
    if n == 1:
        return ["0", "1"]
    prev_gray = generate_gray_code(n - 1)
    return ["0" + code for code in prev_gray] + \
            ["1" + code for code in reversed(prev_gray)]

def html_kmap(s):
    # Parameter Filtering
    num_inputs = int(math.log2(len(s)))
    if len(s) != 2 ** num_inputs:
        return "ERROR - Invalid data string length. Number of " \
            "characters must be a power of 2."

    # Ensure all characters are valid
    for char in s:
        if char not in "01Xx":
            return "ERROR - Data string contains invalid character." \
                "Use only '0', '1', 'x', or 'X'."

    # Generate row and column codes
    num_vars = num_inputs // 2  # Split variables between rows and columns
    num_cols = num_inputs - num_vars

    row_labels = generate_gray_code(num_vars)
    col_labels = generate_gray_code(num_cols)
  
    # Configure table layout
    table = "<table style='border: 1px solid black; border-collapse:" \
        " collapse; text-align: center;'>"

    # Generate input labels
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    rbits = alphabet[0:num_inputs//2]
    cbits = alphabet[num_inputs//2 : num_inputs]
    table += f"<tr><th style='padding: 10px;'>\\ {cbits} <br> \\ <br>" \
        f"{rbits} \\<br></th>"

    # Generate column headers
    for col in col_labels:
        table += f"<th style='border: 1px solid black; padding: " \
            f"10px;'> {col} </th>"
    table += "</tr>"

    # Fill in K-map values
    for r, row_label in enumerate(row_labels):
        table += f"<tr><th style='border: 1px solid black; " \
            f"padding: 10px;'> {row_label} </th>"
            
        for c, col_label in enumerate(col_labels):
            index = int(row_label + col_label, 2)  # Convert Gray code to index
            char = s[index] if index < len(s) else "X;"
            table += f"<td style='border: 1px solid black;'>{char}</td>"
        table += "</tr>"

    table += "</table>"
    return table

# Example usage
html_output = html_kmap("011X11X0")
print(html_output)
with open("output.html", "w") as file:
    file.write(html_output)

html_output2 = html_kmap("011X11X011010110")
print(html_output2)
with open("output2.html", "w") as file:
   file.write(html_output2)
