#!/bin/python3

from math import floor, log10

def position_of_significant_digit(x, n):
    if x == 0:
        mag = 0
    else:
        mag = int(floor(log10(abs(x))))
    if mag >= 0:
        return mag - n + 1
    return   -n 

def round_to_n(x,n,as_string=False):
    pos = position_of_significant_digit(x,n)
    rounded =  int ((x * 10**-pos +.5)) / (10**-pos)
    if not as_string:
        return rounded
    i,d = f"{rounded}".split(".")
    if len(i) >= n:
        return i
    elif i == "0":
        return "0." + d[0:n]
    else:
        return i + "." + d[0:n-len(i)]


def regex_match_number(x,n,exact):
    a = f'{x:f}'
    if "." not in a:
        a = a + '.'
    a = a + "0"*n
    if x == 0 and not exact:
        return "0.|0(.0*)?"
    if a[0:2] == "0." and exact:
        r = "0?"+a[1:2+n]+"([0-4]\\d*)?"
    elif a[0:2] == "0.":
        r = "0?"+a[1:2+n]+"([0-4]\\d*)?"
        a = a[1:2+n]
        if a[-1] == "0":
            while a[-1]=="0":
                a = a[:-1]
            r = r + "|0?"+a+"0*"
    elif '.' in a[0:n]:
        r = a[0:1+n]+"([0-4]\\d*)?"
        a = a[0:1+n]
        if a[-1] == "0":
            while a[-1]=="0":
                a = a[:-1]
            if a[-1] == ".":
                r = r + "|0?"+a[0:-1]+"(.0*)?"
            else:
                r = r + "|0?"+a+"0*"
    else:
        i,d = a.split('.')
        r = a[0:n] 
        if len(i) == n:
            r = i + "(.|.[0-4]\\d*)?"
        elif len(i) == n+1:
            r = i[0:n] + "[0-4]" + "(.\\d*)?"
        else:
            r = i[0:n] + "[0-4]" + "\\d{" + f"{len(i)-n-1}" + "}(.\\d*)?"
    r = r.replace(".", "\\.")
    return r

def regex_match_next_number(x,n):
    a = f'{x:f}'
    if "." not in a:
        a = a + '.'
    a = a + "0"*n
    if a[0:2] == "0.":
        r = "0?" + a[1:2+n]+"[5-9](\\d*)?"
    elif '.' in a[0:n]:
        r = a[0:1+n]+"[5-9](\\d*)?"
    else:
        i,d = a.split('.')
        r = a[0:n] 
        if len(i) == n:
            r = i + ".[5-9]\\d*"
        elif len(i) == n+1:
            r = i[0:n] + "[5-9]" + "(.\\d*)?"
        else:
            r = i[0:n] + "[5-9]" + "\\d{" + f"{len(i)-n-1}" + "}(.\\d*)?"
    r = r.replace(".", "\\.")
    return r
    
    
def regex_match_significant_digits(x, n, exact = False):
    if n < 1 or int(n) != n:
        return f"\\d*.?\\d*"
    a = round_to_n(x, n)
    b = round_to_n( a - 10 ** (position_of_significant_digit(x,n)-1), n+1 )
    if a != 0:
        return regex_match_number(a, n, exact) + "|" + regex_match_next_number(b, n)  
    else:
        return regex_match_number(a, n, exact)

"""
tests = [ 
         (1.25, 2, ["1.3", "1.31", "1.34", "1.344445", "1.25", "1.26", "1.28", "1.29999"] ),
         (1.25, 1, ["1.03", "1.031", "1.034", "1.0344445", "1.025", "1.026", "1.028", "1.029999"] ),
         (.25, 3, [".25", ".250",".2501",".2499"] ),
         (250653, 3, ["251000","250699","251499"] ),
         ]
for test in tests:
    print( "testing: ",test[0], test[1])
    regex = regex_number(test[0], test[1])
    print(regex)
    matches = test[2]
    expr = re.compile(regex)
    for answer in matches: 
        print(answer)
        if expr.match(answer)[0] != answer:
            pass
"""

