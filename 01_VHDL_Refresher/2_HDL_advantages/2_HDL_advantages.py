import d2l
import random

pool = d2l.QuestionPool( "HDL Advantages", "pool.csv" )

hdl_adv = {
    "It provides a uniform language to communicate designs" : 1,
    "It allows the designer to work at a higher level of abstraction" : 1,
    "It enables testing, debugging, and simulation of a system before any hardware is built" : 1,
    "It is easier to maintain/update/modify design" : 1,
    "It allows one design to be implemented in any suitable technology" : 1,
    "It allows the designers to choose the exact circuit structure of the resulting implementation" : 0,
    "It is easier for beginners to understand" : 0,
    "It is visually intuitive, allowing the user to view logic as it's being built": 0,
    "HDL Guarantees a one-to-one correspondence between the written code and the synthesized hardware, "
    "decreasing the risk of unintended hardware such as latches" : 0

}

for i in range(8):
    choices = random.sample( sorted(hdl_adv) , 6)

    qtext = "Which of the following is are an advantage of " \
            " using a HDL over directly designing circuits at " \
            " the gate level."
    
    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for adv in choices:
        question.add_answer(adv, hdl_adv[adv])
    pool.add_question( question )

pool.package()

