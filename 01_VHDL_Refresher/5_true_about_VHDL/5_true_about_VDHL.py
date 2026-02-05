import d2l
import random

pool = d2l.QuestionPool( "True statements about VHDL", "pool.csv" )

vhdl_statement = {
    "VHDL is strongly typed": 1,
    "VHDL is case insensitive": 1,
    "VHDL is a freeform language, meaning that the type of whitespace you use is irrelevant": 1,
    "All VHDL language standards have inline comments that begin with --": 1,
    "VHDL supports user-defined types": 1,
    "VHDL allows multi-line comments using /* ... */": 1,
    "VHDL is commonly used to model and design digital hardware": 1,
    "Entity/architecture separate interface from implementation": 1,
    "Generics can parameterize designs (like width, depth, constants)": 1,
    "Not all VHDL code is synthesizable": 1,
    "You can start an identifier with a number in VHDL": 0,
    "The := operator assigns to signals": 0,
    "VHDL is mainly used for analog circuit design": 0,
    "All VHDL designs must use std_logic": 0,
    "VHDL always infers hardware exactly as written": 0,
    "VHDL requires indentation, similar to languages like Python": 0,
    "VHDL is dynamically typed": 0,
    "begin is optional in VHDL architectures": 0,
    "VHDL does not support if-statements": 0,
    "VHDL automatically converts types for you (like integer <-> std_logic_vector without conversion)": 0
}

for i in range(11):
    choices = random.sample( sorted(vhdl_statement) , 4)

    qtext = "Which of the following are true statements" \
            " about the VHDL landuage?"
    
    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for vhdl in choices:
        question.add_answer( vhdl, vhdl_statement[vhdl])
    pool.add_question( question )

pool.package()
