import d2l
import random

pool = d2l.QuestionPool("Find the syntax error in signal assignment", "pool.csv")

syntax_error= {
    "sig_a was never defined as a port or a signal.": 1,
    "sig_a has type std_logic, which doesn't match the type of the literal 0": 1,
    "sig_a has type std_logic_vector, which doesn't match the type of the literal 0": 1,
    "sig_a is an invalid identifier": 0,
    "sig_a has already been assigned a driver  somewhere else": 1,
    "<= is nto a valid assignment operator in VHDL": 0
}

for i in range(6):
    choices = random.sample( sorted(syntax_error) , 5)

    qtext = qtext = """The signal assignment below appears in the VHDL description of a
    circuit. The assignment is flagged as having a syntax error. Which of the
    following could be wrong with the signal assignment? Select all that could be
    wrong. Recall that a syntax error is a violation of the rules of a language,
    not a logical bug.

    sig_a <= 0;
    """

    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for error in choices:
        question.add_answer(error, syntax_error[error])
    pool.add_question( question )

pool.package()