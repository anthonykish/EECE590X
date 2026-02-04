import re
from logic_utils import qm2

def logic_eval(inputs, input_values, expression):
    
    """
    Evaluates a Boolean expression to return either 0 or 1.

    inputs: list of inputs like ["a", "b", "c"]
    input_combo: string or list w/ current combination of those inputs,
    like "101", meaning a=1, b=1, c=1
    expression: Boolean expression like like "(a + bc)'"
    """

    # Empty strings just return 1 (think about FSM arcs with no labels)
    if not expression:
        return 1

    expression = to_bitwise(inputs, expression)

    # Convert from string to list if necessary
    if type(input_values) == str:
        input_values = [i for i in input_values]

    # Replace inputs with their current values of 0 or 1
    for i, iv in zip(inputs, input_values):
        expression = expression.replace(i, iv)
    
    output = eval(expression)

    # isolate LSB to avoid weird Python integer jank
    output &= 1

    return output

def to_bitwise(inputs, expression):
    
    """
    Turns a typical Boolean algebra expression (like (a + bc)') into its
    bitwise operation form

    inputs: list of inputs like ["a", "b", "c"]
    expression: string for Boolean expression like "(a + bc)'"

    returns: "Bitwise Boolean" expression like "~(a+b&c)"
    """

    # Purge expression of spaces
    expression = expression.replace(" ", "")

    # Artificially put *s in places where the AND is implied
    for i in inputs:
        expression = re.sub(rf"\)('?){i}", rf")\1*{i}", expression)
        expression = re.sub(rf"{i}('?)\(", rf"{i}\1*(", expression)
        # Gotta account for combos of multiple inputs
        for j in inputs:
            expression = re.sub(rf"{i}('?){j}", rf"{i}\1*{j}", expression)

    # If ' appears after a term, move it before
    # ex: ab' -> a'b
    # LEAVE A SPACE SO BELOW ALGORITHM DOESN'T PICK UP THE )' PATTERN
    for i in inputs:
        expression = re.sub(f"{i}'", f" '{i}", expression)

    # If ' appears after (), move it before the appropriate group
    # ex: (a+(b)')' -> '(a+'(b))
    
    # expression = re.sub(r"(\(.*\))'", r"'\1", expression) # for outer 
    # expression = re.sub(r"(\([^(]*?\))'", r"'\1", expression) # for inner
    for i in range(1, len(expression)):
        if expression[i] == "'" and expression[i-1] == ")":
            j = i-1
            paren_depth = 1
            while paren_depth > 0:
                j -= 1
                if expression[j] == ")":
                    paren_depth += 1
                elif expression[j] == "(":
                    paren_depth -= 1
            expression = expression[:j] + "'" + expression [j:i] + expression[i+1:]

    # Purge expression of spaces AGAIN
    expression = expression.replace(" ", "")

    # Finally replace the operators with their bitwise equivalents
    expression = expression.replace("'", "~") # NOT
    expression = expression.replace("+", "|") # OR
    expression = expression.replace("*", "&") # AND
                                # ^ as XOR is fine

    return expression

def to_english(inputs, expression):
    
    """
    Turns a typical Boolean algebra expression (like (a + bc)') into its
    English form

    inputs: list of inputs like ["a", "b", "c"]
    expression: string for Boolean expression like "(a + bc)'"

    returns: English expression like "not (a or b and c)"
    """

    # Purge expression of spaces
    expression = expression.replace(" ", "")

    # Artificially put *s in places where the AND is implied
    for i in inputs:
        expression = re.sub(rf"\)('?){i}", rf")\1*{i}", expression)
        expression = re.sub(rf"{i}('?)\(", rf"{i}\1*(", expression)
        # Gotta account for combos of multiple inputs
        for j in inputs:
            expression = re.sub(rf"{i}('?){j}", rf"{i}\1*{j}", expression)

    # If ' appears after a term, move it before
    # ex: ab' -> a'b
    # LEAVE A SPACE SO BELOW ALGORITHM DOESN'T PICK UP THE )' PATTERN
    for i in inputs:
        expression = re.sub(f"{i}'", f" '{i}", expression)

    # If ' appears after (), move it before the appropriate group
    # ex: (a+(b)')' -> '(a+'(b))
    
    # expression = re.sub(r"(\(.*\))'", r"'\1", expression) # for outer 
    # expression = re.sub(r"(\([^(]*?\))'", r"'\1", expression) # for inner
    for i in range(1, len(expression)):
        if expression[i] == "'" and expression[i-1] == ")":
            j = i-1
            paren_depth = 1
            while paren_depth > 0:
                j -= 1
                if expression[j] == ")":
                    paren_depth += 1
                elif expression[j] == "(":
                    paren_depth -= 1
            expression = expression[:j] + "'" + expression [j:i] + expression[i+1:]

    # Purge expression of spaces AGAIN
    expression = expression.replace(" ", "")

    # Finally replace the operators with their bitwise equivalents
    expression = expression.replace("'", " not ")
    expression = expression.replace("+", " or ")
    expression = expression.replace("*", " and ")
    expression = expression.replace("^", " xor ")

    return expression

def optimized_sop(inputs, output_column, treat_dc_like_0 = False):
    
    """
    Quine-McCluskey optimized sum of products finder
    This is basically a wrapper for the qm2 file that adds named inputs and outputs

    Arguments:
    inputs: list of ordered input names like ["a", "b", "c", "d"]
    output_column: output truth table column like "1010001110100011"

    Returns:
    optimized sum of products in Boolean form like "bc + b'd'"    
    """

    ones, zeros, dc = [], [], []

    for i in range(len(output_column)):
        if output_column[i] == "1":
            ones.append(i)
        elif output_column[i] == "0" or (output_column[i] == "x" and treat_dc_like_0):
            zeros.append(i)
        elif output_column[i].lower() == "x":
            dc.append(i)
    
    # Outputs a list like ['X0X0', 'X11X']
    qm2_output = qm2.qm(ones, zeros, dc)

    # Convert these to Boolean algebra form with the inputs
    terms = []
    for qm_term in qm2_output:

        term = ""

        for input, char in zip(inputs, qm_term):
            if char == "1":
                term += input
            elif char == "0":
                term += f"{input}'"
            # For don't care, just don't include the letter
    
        terms.append(term)
    
    sop = " + ".join(terms)

    return sop

def opposite(inputs, expression):

    """
    Finds the optimized expression which is the opposite (negation) of the
    one given.

    Arguments:
    inputs: list of ordered input names like ["a", "b", "c", "d"]
    expression: Boolean expression like "a + bc'"

    Returns:
    optimized sum of products in Boolean form (string) 
    """

    # Make all possible combinations of inputs
    num_inputs = len(inputs)
    input_combos = [f"{i:0{num_inputs}b}" for i in range(2 ** num_inputs)] 

    # Build the output column
    col = ""
    for input_combo in input_combos:
        col += str(logic_eval(inputs, input_combo, expression))

    # Invert the output column (sorta like a swapping algorithm)
    col = col.replace("1", "-")
    col = col.replace("0", "1")
    col = col.replace("-", "0")

    # Make the new expression
    return optimized_sop(inputs,  col)

def b_format(num, width):

    """
    Formats a number as a binary string. Negatives get two's complement

    num: number to format
    width: bit width
    """

    all_1s = (1 << width) - 1

    # Masking and formatting must be done on same line
    out = f"{(num & all_1s):0{width}b}"

    return out

def h_format(num, width):

    """
    Formats a number as a hexadecimal string. Negatives get two's complement

    num: number to format, can be binary string or regular int
    width: hex width
    """
    
    all_1s = (1 << (width*4)) - 1

    # Masking and formatting must be done on same line
    out = f"{(num & all_1s):0{width}x}"

    out = out.upper()

    return out 

def to_decimal(binary):
    # turns binary string to decimal
    return int(binary, 2)
    