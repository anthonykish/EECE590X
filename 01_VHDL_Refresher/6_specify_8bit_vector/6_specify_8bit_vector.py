import d2l
import random

pool = d2l.QuestionPool("Valid ways in VHDL to specify 8-bit std_logic_vectors", "pool.csv")

bits = {
    "100": 0,
    '"100"': 0,
    '"00000100"': 0,
    '"1100100"': 0,
    '"0100100"': 1,
    '8b"1100100"': 1,
    '8h"64"': 1,
    '8d"100"': 1,
    '"0110_0100"': 1,
    'B"01100100"': 1,
    '8B"01100100"': 1,
    '8B"1100100"': 1,
    'B"1100100"': 0,
    '"_01100100"': 0,
    '"0110__0100"': 0
}

for i in range(10):
    choices = random.sample( sorted(bits) , 9)

    qtext = "Which of the following are valid ways in VHDL to" \
    " specify an 8-bit std_logic_vector literal with value equal" \
    " to decimal 100?"
    
    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for bit in choices:
        question.add_answer(bit, bits[bit])
    pool.add_question( question )

pool.package()