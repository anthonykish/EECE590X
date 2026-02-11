import d2l
import random

pools = d2l.QuestionPool("Valid VHDL Dataflows", "pool.csv")

correct_dataflows = {
    "f1 <= a AND b AND NOT c AND NOT e;": 1,
    "f3 <= a XOR b XOR x XOR d;": 1,
    "f4 <= a XNOR b XNOR d XNOR e;": 1,
    "f6 <= c NOR (d NOR e);": 1,
    "f7 <= (a NAND (b AND c)) AND d;": 1,
    "f8 <= NOT (a AND b);": 1,
    "f9 <= (a AND b) OR (c AND d);": 1,
    "f10 <= (a NAND b) OR (c NAND d);": 1,
    "f11 <= (a OR b) AND (NOT c);": 1,
    "f12 <= (a XOR b) AND (d OR e);": 1,
}

wrong_dataflows = {
    "f2 <= a AND b AND c OR d;": 0,
    "f5 <= a NAND b NAND c;": 0,
    "f13 <= a AND;": 0,
    "f14 <= NOT;": 0,
    "f15 <= a XOR XOR b;": 0,
    "f16 <= (a OR b)) AND c;": 0, 
    "f17 <= (a AND b;": 0,
    "f18 <= a AND (b OR);": 0
}

for i in range(20):
    num = random.randint(1, 5)

    choices = random.sample( sorted(correct_dataflows) , num) + random.sample( sorted(wrong_dataflows) , 6-num)

    qtext = "Which VHDL dataflow statements are valid? Select all that apply."

    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for choice in choices:
        if choice in correct_dataflows:
            question.add_answer(choice, correct_dataflows[choice])
        else:
            question.add_answer(choice, wrong_dataflows[choice])
    pools.add_question( question )

pools.package()

