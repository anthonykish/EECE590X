import d2l
import random

pool = d2l.QuestionPool("Reducing with Boolean Properties MAT", "pool.csv")

number_questions = 50

equations = {"(a + b)' + (a + c)'"      : "a'(b' + c')",
             "a(a' + b' + c')"          : "a(b' + c')",
             "a + abc"                  : "a",
             "b(a + b + c)"             : "b",
             "abc + c"                  : "c",
             "(bc)(cb)"                 : "bc",
             "a'a + (bc)'"              : "(bc)'",
             "a' * (a' + b + c'c)"      : "a'",
             "b' * (a' + b + c' + c)"   : "b'",
             "(a + b)(b + a)"           : "a + b",
             "a'a * (b + c)"            : "0",
             "a + a'(a' + c)"           : "1"
             }

for i in range(number_questions):
    answers = random.sample(sorted(equations), 4)

    question_text = "Match the following expressions to their reduced forms."
    
    question = d2l.MQuestion(question_text)

    for j in answers:
        question.add_answer(j, equations[j])

    pool.add_question(question)

pool.dump()
pool.package()
