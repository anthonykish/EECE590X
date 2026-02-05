import d2l
import random

pool = d2l.QuestionPool( "Determine valid signal names", "pool.csv" )

sig_names = {
    "a_b_c" : 1,
    "b2" : 1,
    "sig_b" : 1,
    "divisor_1": 1,
    "divisor2": 1,
    "three_a" : 1,
    "3a" : 0,
    "_sig_a" : 0,
    "sig__c" : 0,
    "1signal" : 0,
    "newSig!" : 0,
    "one-two": 0
}

for i in range(11):
    choices = random.sample( sorted(sig_names) , 7)

    qtext = "Which of the following are valid names" \
            " for VDHL signals?"
    
    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for sig in choices:
        question.add_answer( sig, sig_names[sig])
    pool.add_question( question )

pool.package()
