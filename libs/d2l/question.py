#!/bin/python -B
#Doug Summerville, Binghamton University
#BlackBoard Question Classes

from random import shuffle
import re
from .sigfigs import regex_match_significant_digits

def html_attribute(text):
    is_html=re.compile(r"</?\s*[a-z-][^>]*\s*>|(\&(?:[\w\d]+|#\d+|#x[a-f\d]+);)")
    if is_html.match(text):
        return "HTML"
    else:
        return "NOT HTML"

class Question(object):
    def __init__(self,qtype="",title="",text="",points=10,difficulty=1):
        self.set_type(qtype)
        self.set_title(title)
        self.set_question_text(text)
        self.set_points(points)
        self.set_difficulty(difficulty)
        self.answers=[]
        self.shuffle=False;

    def add_image(self,image):
        self.Image=(image)

    def add_hint(self,text):
        self.Hint=(text,html_attribute(text))

    def add_feedback(self,text):
        self.Feedback=(text,html_attribute(text))

    def set_title(self,title):
        self.Title=(title)

    def title(self):
        return self.Title

    def set_type(self,qtype):
        assert( qtype in {"TF","MC","SA","NSA","M","MS"} )
        self.NewQuestion=qtype

    def type(self):
        return self.NewQuestion

    def set_question_text(self,text):
        self.QuestionText=(text,html_attribute(text))

    def text(self):
        return self.QuestionText

    def set_points(self,points):
        self.Points=points

    def points(self):
        return self.Points

    def set_difficulty(self,difficulty):
        self.Difficulty=difficulty

    def difficulty(self):
        return self.Difficulty

    def dump(self):
        for m in ("NewQuestion","Title","QuestionText","Points","Difficulty","Image","shuffle","Feedback","Scoring","Hint"):
            if not hasattr(self,m):
                continue
            print(m,": ",getattr(self,m))
        for a in self.answers:
            print(a)

    def write_to_csv(self,writer,title=""):
        if title != "":
            self.set_title(title)
        for m in ("NewQuestion","Title","QuestionText","Points","Difficulty","Image","Hint","Feedback","Scoring"):
            if m == "answers":
                continue
            if not hasattr(self,m):
                continue
            if type(getattr(self,m)) is tuple:
                writer.writerow([m]+list(getattr(self,m)))
            else:
                writer.writerow([m]+[getattr(self,m)])
        if self.shuffle:
            shuffle(self.answers)
        for a in self.answers:
            writer.writerow(a)
        writer.writerow([])

    def checks_out(self):
        if not self.answers: #has at least one answer
            return False
        return True

class TFQuestion(Question):
    def __init__(self,text="",points=10,difficulty=1,title=""):
        super().__init__("TF",title,text,points,difficulty)
    def add_answer(self,value=True,incorrect_percent=0):
        if value is True:
            self.answers.append(("TRUE",100))
            self.answers.append(("FALSE",incorrect_percent))
        else:
            self.answers.append(("TRUE",incorrect_percent))
            self.answers.append(("FALSE",100))

#todo verify that one answer is 100 and others are 0-99
class MCQuestion(Question):
    def __init__(self,text="",points=10,difficulty=1,title="",shuffle=True):
        super().__init__("MC",title,text,points,difficulty)
        if shuffle:
            self.shuffle=True
    def add_answer(self,text="",points=0):
            self.answers.append(("OPTION",points,text,"HTML"))

#todo verify that one answer is 100 and others are 0-99
class MSQuestion(Question):
    def __init__(self,text="",points=10,difficulty=1,title="",shuffle=True,scoring="RightAnswers"):
        super().__init__("MS",title,text,points,difficulty)
        self.Scoring = scoring
        if shuffle:
            self.shuffle=True
    def add_answer(self,text="",is_correct=True):
            self.answers.append(("OPTION",1 if is_correct else 0,text,"HTML"))

class SAQuestion(Question):
    def __init__(self,text="",points=10,difficulty=1,title=""):
        super().__init__("SA",title,text,points,difficulty)
    def add_answer(self,text="",points=100,is_regex=False):
        if is_regex:
            self.answers.append(("ANSWER",points,text,"regexp"))
        else:
            self.answers.append(("ANSWER",points,text))

class NSAQuestion(Question):
    def __init__(self,text="",points=10,difficulty=1,title=""):
        super().__init__("SA",title,text,points,difficulty)
    def add_answer(self,value=1.0, sigfigs=2, whole=True, units = "", exact=False ,points=100):
            text = regex_match_significant_digits(value, sigfigs, exact )
            if units != "":
                text = text +f"\\s*{units}"
            if whole:
                text = "^\\s*"+text+"\\s*$"
            self.answers.append(("ANSWER",points,text,"regexp"))

class MQuestion(Question):
    def __init__(self,text="",points=10,difficulty=1,title="",shuffle=False,scoring="EquallyWeighted"):
        super().__init__("M",title,text,points,difficulty)
        self.shuffle=shuffle 
        self.Scoring=scoring
    def add_answer(self,match="",choice="",points=10):
        assert choice, "Must specify choice value"
        self.answers.append((match,choice))
    def write_to_csv(self,writer,title=""):
        if title != "":
            self.set_title(title)
        for m in ("NewQuestion","Title","QuestionText","Points","Difficulty","Image","Hint","Feedback","Scoring"):
            if not hasattr(self,m):
                continue
            if type(getattr(self,m)) is tuple:
                writer.writerow([m]+list(getattr(self,m)))
            else:
                writer.writerow([m]+[getattr(self,m)])
        choice_list= list(dict.fromkeys([ a[1] for a in self.answers ] ))
        if self.shuffle:
            shuffle(choice_list)
        for i,choice in enumerate(choice_list):
             writer.writerow(["Choice",1+i,choice])
        
        #matches are made unique if two are added
        match_list = { a[0]:a[1] for a in self.answers if a[0] }
        for match in match_list:
            choice = choice_list.index(match_list[match])+1
            writer.writerow(["Match",choice,match])
        writer.writerow([])

#//ORDERING QUESTION TYPE            
#//Items must include text in column2            
#NewQuestion O       
#ID  CHEM110-240     
#Title   This is an ordering question        
#QuestionText    This is the question text for O1        
#Points  2       
#Difficulty  2       
#Scoring RightMinusWrong     
#Image   images/O1.jpg       
#Item    This is the text for item 1 NOT HTML    This is feedback for option 1
#Item    This is the text for item 2 HTML    This is feedback for option 2
#Hint    This is the hint text       
#Feedback    This is the feedback text       

