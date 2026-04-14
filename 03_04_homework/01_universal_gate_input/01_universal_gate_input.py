import d2l
import random

pools = d2l.QuestionPool("Universal gate input combinational logic functions", "pool.csv")


for i in range(20):

    gate = {
    "LUT3": 3,
    "LUT4": 4,
    "LUT5": 5,
    "LUT6": 6,
    "8:1 MUX": 3,
    "16:1 MUX": 4,
    "32:1 MUX": 5,
    "64:1 MUX": 6,
    "8x1 RAM": 3,
    "16x1 RAM": 4,
    "32x1 RAM": 5,
    "64x1 RAM": 6,
    "8x1 ROM": 3,
    "16x1 ROM": 4,
    "32x1 ROM": 5,
    "64x1 ROM": 6
    }
    
    choices = random.sample( sorted(gate) , 9)

    input = random.randint(3, 6)

    for index in choices:
        if input <= gate[index]:
            gate[index] = 1
        else:
            gate[index] = 0

    qtext = "<p><table style='border-collapse: collapse; text-align: center'><tr>    <th style='border-bottom: 2px solid black; padding: 15px;'>Q1</th>    <th style='border-bottom: 2px solid black; padding: 15px;'>Q0</th>    <th style='border-bottom: 2px solid black; padding: 15px;'>a</th>    <th style='border-bottom: 2px solid black; padding: 15px;'>b</th>    <th style='border-bottom: 2px solid black; padding: 15px;'>Q1+</th>    <th style='border-bottom: 2px solid black; padding: 15px;'>Q0+</th>    <th style='border-bottom: 2px solid black; padding: 15px;'>F</th>    <th style='border-bottom: 2px solid black; padding: 15px;'>G</th></tr>  <tr>    <td>0</td>    <td>0</td>    <td>0</td>    <td>0</td>    <td style='border-left: 2px solid black;'>0</td>    <td>0</td>    <td>0</td>    <td>0</td></tr>  <tr>    <td>0</td>    <td>0</td>    <td>0</td>    <td>1</td>    <td style='border-left: 2px solid black;'>0</td>    <td>1</td>    <td>0</td>    <td>0</td></tr>  <tr>    <td>0</td>    <td>0</td>    <td>1</td>    <td>0</td><|start_of_edit|></p>"
    
    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )

    for index in choices:
        question.add_answer( index, gate[index])
    pools.add_question( question )

pools.package()
