#Doug Summerville, Binghamton University
#D2L Question Pool Class

import csv

class QuestionPool():

    def __init__(self,title="question pool",csvfname="pool.csv"):
        self.numberquestions=0
        self.csvfname=csvfname
        self.title=title
        self.questionlist=[]

    def add_question(self,question):
        assert question.checks_out()
        self.questionlist.append(question)
        self.numberquestions=self.numberquestions+1

    def dump( self):
        for q in self.questionlist:
            q.dump()
            print("")

    def package(self):
        self.write_csv_file();

    def write_csv_file(self):
        with open( self.csvfname, 'w', newline='') as csvfile:       
             writer=csv.writer( csvfile,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
             for q in self.questionlist:
                 q.write_to_csv(writer,title=self.title)
                 writer.writerow([])

