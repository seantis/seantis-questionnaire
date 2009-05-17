from questionnaire import *
from django.utils.translation import ugettext as _

@question_proc('range')
def question_range(request, question):
    cd = question.getcheckdict()
    Range = cd.get('range', '1-5')
    try:
        rmin, rmax = Range.split('-', 1)
        rmin, rmax = int(rmin), int(rmax)
    except ValueError:
        rmin = 0
        rmax = int(range)
    selected = int(request.POST.get('question_%s' % question.number, rmin))
    Range = range(rmin, rmax+1)
    return {
        'required' : True,
        'range' : Range,
        'selected' : selected,
    }

@answer_proc('range')
def process_range(question, answer):
    checkdict = question.getcheckdict()
    try:
        rmin,rmax = checkdict.get('range','1-10').split('-',1)
        rmin, rmax = int(rmin), int(rmax)
    except:
        raise AnswerException("Error in question. Additional checks field should contain range='min-max'")
    try:
    	ans = int(answer['ANSWER'])
    except:
	raise AnswerException("Could not convert `%r` to integer.")
    if ans > rmax or ans < rmin:
        raise AnswerException(_(u"Out of range"))
    return ans
add_type('range', 'Range of numbers [select]')



