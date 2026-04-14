import d2l
import random

pools = d2l.QuestionPool("Correct expansions of boolean equations", "pool.csv")

expansions = {
    "a'(b'c+b'c')+a(bc+b'c)": 1,
    "b'(c+a'c')+b(ac)": 1,
    "c'(a'b')+c(ab+b')": 1,
    "a'(b'c+b'c')+a(bc)": 0,
    "a'(b'c')+a(bc)": 0,
    "ac + a'b'": 1,
    "a(c) + a'(b')": 1,
    "a' b' + a c": 1,
    "(a + b')c + a'b'c'": 1,
    "c(a + b') + a'b'c'": 1,
    "b'(a' + c) + abc": 1,
    "a' (b'c + b'c') + a(c)": 1,
    "ac + a'b'c'": 0,
    "c(a + b')": 0,
    "a'b'c' + b'c": 0,
    "a' b' + c": 0,
    "ac + b'": 0,
    "(a + b')c": 0,
    "b'(c + a'c') + b(ac)": 0
}

for i in range(50):
    choices = random.sample( sorted(expansions) , 5)

    qtext = "Which are correct expansions of the following Boolean equation?" \
    " Select all that apply. f <= abc + b'c + a'b'c'"
    
    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for choice in choices:
        question.add_answer( choice, expansions[choice])
    pools.add_question( question )

pools.package()