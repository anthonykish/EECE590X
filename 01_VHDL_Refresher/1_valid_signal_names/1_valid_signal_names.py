import d2l
import random

pool = d2l.QuestionPool( "Determine valid signal names", "pool.csv" )

sig_names = {
    "a_b_c" : "Valid",
    "b2" : "Valid",
    "sig_b" : "Valid",
    "divisor_1": "Valid",
    "divisor2": "Valid",
    "three_a" : "Valid",
    "3a" : "Not Valid",
    "_sig_a" : "Not Valid",
    "sig__c" : "Not Valid",
    "1signal" : "Not Valid",
    "newSig!" : "Not Valid",
    "one-two": "Not Valid"
}

for i in range(11):
    choices = random.sample( sorted(sig_names) , 7)

    qtext = "Which of the following are valid names" \
            "for VDHL signals?"
    
    question = d2l.MQuestion( text=qtext, points=10, shuffle=True )

    for sig in choices:
        question.add_answer( sig, sig_names[sig])
    pool.add_question( question )

pool.package()
