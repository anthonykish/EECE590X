import random
import d2l
from html_tt import html_tt
import re


pools = d2l.QuestionPool("Convert truth table to hex", "pool.csv")


for i in range(20):
    fTT = ""
    for f in range(16):
        fTT += str(random.randint(0, 1))

    # ttValues = ["0000000011111111", "0000111100001111", "0011001100110011", "0101010101010101", fTT]

    truth_table = html_tt(fTT, ["A", "B", "C", "D", "f"])
    # truth_table = html_tt(["0011", "0101"], ["A", "B", "C", "f"])

    rev = fTT[::-1]  # reverse whole 16-bit string
    nibbles = [rev[i:i+4] for i in range(0, len(rev), 4)]
    hex_str = "".join(format(int(n, 2), "X") for n in nibbles)

    pattern = f'(?i)(0x|16x)?"*{hex_str}"*\s*$'


    qtext = f"<p> A truth table for a function is given below. " \
            f"{truth_table} What would be the contents of the LUT, " \
            f"in hexadecimal? Assume the truth table is converted " \
            f"to hex from last to first entry. <p>"   
    
    question = d2l.SAQuestion(text=qtext, points=10)

    question.add_answer(pattern, is_regex=True)
    pools.add_question(question)

pools.package()

