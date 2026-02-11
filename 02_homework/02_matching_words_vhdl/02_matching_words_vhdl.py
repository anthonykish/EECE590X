import d2l
import random

pool = d2l.QuestionPool("Match the words with their descriptions", "pools.csv")

matches = {
    "netlist": "(a)",
    "synthesis": "(b)",
    "circuit": "(c)",
    "logic primitives": "(d)"
}

for i in range(10):
    choices = random.sample( sorted(matches) , 4)

    qtext = "<p> A <u>(a)</u>, in the context of FPGA <u>(b)</u>, is a text-based " \
    "representation of a <u>(c)</u> after its HDL description has been synthesized, " \
    "that describes the <u>(d)</u> that will be used to implement the circuit " \
    "and how they are interconnected. </p>" \
    
    question = d2l.MQuestion( text=qtext, points=10, shuffle=True )

    for match in choices:
        question.add_answer(match, matches[match])
    pool.add_question( question )

pool.package()