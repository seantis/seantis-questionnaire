from questionnaire import *
from django.conf.urls.static import settings
from django.utils.translation import ugettext as _
from django.utils.simplejson import dumps

@question_proc('range')
def question_range(request, question):
    cd = question.getcheckdict()
    
    rmin, rmax = parse_range(cd)
    rstep = parse_step(cd)
    runit = cd.get('unit', '')
    
    current = request.POST.get('question_%s' % question.number, rmin)

    return {
        'required' : True,
        'rmin' : rmin,
        'rmax' : rmax,
        'rstep' : rstep,
        'runit' : runit,
        'current' : current,
        'jsinclude' : [settings.STATIC_URL+'range.js']
    }

@answer_proc('range')
def process_range(question, answer):
    cd = question.getcheckdict()

    rmin, rmax = parse_range(cd)
    rstep = parse_step(cd)

    convert = range_type(rmin, rmax, rstep)

    try:
    	ans = convert(answer['ANSWER'])
    except:
	   raise AnswerException("Could not convert `%r`")
    
    if ans > convert(rmax) or ans < convert(rmin):
        raise AnswerException(_(u"Out of range"))

    return dumps([ans])

add_type('range', 'Range of numbers [select]')

def parse_range(checkdict):
    "Given a checkdict for a range widget return the min and max string values."

    Range = checkdict.get('range', '1-5')

    try:
        rmin, rmax = Range.split('-', 1)
    except ValueError:
        rmin, rmax = '1', '5'

    return rmin, rmax

def parse_step(checkdict):
    "Given a checkdict for a range widget return the step as string value."

    return checkdict.get('step', '1')

def range_type(rmin, rmax, step):
    """Given the min, max and step value return float or int depending on
    the number of digits after 0.

    """

    if any((digits(rmin), digits(rmax), digits(step))):
        return float
    else:
        return int

def digits(number):
    "Given a number as string return the number of digits after 0."
    if '.' in number or ',' in number:
        if '.' in number:
            return len(number.split('.')[1])
        else:
            return len(number.split(',')[1])
    else:
        return 0