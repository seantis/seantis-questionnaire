"""
questionnaire - Django Questionnaire App
========================================

Create flexible questionnaires.

Author: Robert Thomson <git AT corporatism.org>
"""

from django.conf import settings
from django.dispatch import Signal
import os, os.path
import imp

__all__ = [ 'question_proc', 'answer_proc', 'add_type', 'AnswerException',
            'questionset_done', 'questionnaire_done', ]

QuestionChoices = []
QuestionProcessors = {} # supply additional information to the templates
Processors = {} # for processing answers

questionset_done = Signal(providing_args=["runinfo", "questionset"])
questionnaire_done = Signal(providing_args=["runinfo", "questionnaire"])

class AnswerException(Exception):
    "Thrown from an answer processor to generate an error message"
    pass


def question_proc(*names):
    """
    Decorator to create a question processor for one or more
    question types.

    Usage:
    @question_proc('typename1', 'typename2')
    def qproc_blah(request, question):
        ...
    """
    def decorator(func):
        global QuestionProcessors
        for name in names:
            QuestionProcessors[name] = func
        return func
    return decorator

def answer_proc(*names):
    """
    Decorator to create an answer processor for one or more
    question types.
    
    Usage:
    @question_proc('typename1', 'typename2')
    def qproc_blah(request, question):
        ...
    """
    def decorator(func):
        global Processors
        for name in names:
            Processors[name] = func
        return func
    return decorator

def add_type(id, name):
    """
    Register a new question type in the admin interface.
    At least an answer processor must also be defined for this
    type.
    
    Usage:
        add_type('mysupertype', 'My Super Type [radio]')
    """
    global QuestionChoices
    QuestionChoices.append( (id, name) )


import questionnaire.qprocessors # make sure ours are imported first

add_type('sameas', 'Same as Another Question (put question number (alone) in checks')

for app in settings.INSTALLED_APPS:
    try:
        app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
    except AttributeError:
        continue

    try:
        imp.find_module('qprocessors', app_path)
    except ImportError:
        continue

    __import__("%s.qprocessors" % app)

