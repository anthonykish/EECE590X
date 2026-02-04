import schemdraw
import schemdraw.logic as logic
import itertools
import matplotlib

# Used in next function to determine if a term matches a group and should
# be included.
def term_in_group(term, group):
    return all(g == t or g == '.' for g, t in zip(group, term))

def generate_truth_table(num_vars, groups):
    # If 3 variable, create all possible terms like (000,001,010...)
    terms_of_num_vars_len = [''.join(bits) for bits in itertools.product('01', repeat=num_vars)]
    truth_table = []

    for term in terms_of_num_vars_len:
        for group in groups:
            if term_in_group(term, group):
                truth_table.append((term, '1'))
                break  # No need to check other groups
    return truth_table

def switch_chars(s):
    # Added to switch column and row labels to match other coursework
    if len(s) == 4:
        return s[-2:] + s[:2]
    elif len(s) == 3:
        return s[-2:] + s[0]
    else:
        return s


def draw_kmap(groups_in, filename, var_names='abcd'):
    """
    Draws a K-map using only groups (groups like '11..'), no Xs allowed.

    Args:
        groups (dict): Lists of group -> ['000.', '..01',...]
        filename (str): Output file name like 'simple_kmap' (will be of type PNG)
        var_names (str): String of variable names like 'ABCD'
    """
    color_palette = [
        ('red',    '#ff000033'),
        ('green',  '#00ff0033'),
        ('blue',   '#0000ff33'),
        ('purple', '#80008033'),
        ('orange', '#ffa50033'),
        ('cyan',   '#00ffff33'),
        ('yellow', '#ffff0033')
    ]

    new_var_names = switch_chars(var_names)
    
    groups_temp = []
    groups_out = {}

    groups_temp = [switch_chars(group) for group in groups_in]
        

    for i, item in enumerate(groups_temp):
        color, fill = color_palette[i % len(color_palette)]
        groups_out[item] = {'color' : color, 'fill' : fill}

    num_vars = len(var_names)
    truth_table = generate_truth_table(num_vars, groups_temp)

    # Avoid opening Matplotlib GUI
    matplotlib.use('Agg')

    d = schemdraw.Drawing()
    d.add(logic.Kmap(
        names=new_var_names,
        truthtable=truth_table,
        groups=groups_out
    ))
    d.draw()
    d.save(f'{filename}.png')
