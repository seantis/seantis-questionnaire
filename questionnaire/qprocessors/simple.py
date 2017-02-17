from json import dumps

from django.utils.translation import ugettext as _

from questionnaire import add_type
from questionnaire import answer_proc
from questionnaire import AnswerException
from questionnaire import question_proc


@question_proc('choice-yesno', 'choice-yesnocomment', 'choice-yesnodontknow')
def question_yesno(request, question):
    key = "question_%s" % question.number
    key2 = "question_%s_comment" % question.number
    val = request.POST.get(key, None)
    cmt = request.POST.get(key2, '')
    qtype = question.get_type()
    cd = question.getcheckdict()
    jstriggers = []

    if qtype == 'choice-yesnocomment':
        hascomment = True
    else:
        hascomment = False
    if qtype == 'choice-yesnodontknow' or 'dontknow' in cd:
        hasdontknow = True
    else:
        hasdontknow = False

    if not val:
        if cd.get('default', None):
            val = cd['default']

    checks = ''
    if hascomment:
        if cd.get('required-yes'):
            jstriggers = ['%s_comment' % question.number]
            checks = ' checks="dep_check(\'%s,yes\')"' % question.number
        elif cd.get('required-no'):
            checks = ' checks="dep_check(\'%s,no\')"' % question.number
        elif cd.get('required-dontknow'):
            checks = ' checks="dep_check(\'%s,dontknow\')"' % question.number

    return {
        'required': True,
        'checks': checks,
        'value': val,
        'qvalue': '',
        'hascomment': hascomment,
        'hasdontknow': hasdontknow,
        'comment': cmt,
        'jstriggers': jstriggers,
        'template': 'questionnaire/choice-yesnocomment.html',
    }


@question_proc('open', 'open-textfield')
def question_open(request, question):
    key = "question_%s" % question.number
    value = question.getcheckdict().get('default', '')
    if key in request.POST:
        value = request.POST[key]
    return {
        'required': question.getcheckdict().get('required', False),
        'value': value,
    }


@answer_proc('open', 'open-textfield', 'choice-yesno', 'choice-yesnocomment',
             'choice-yesnodontknow')
def process_simple(question, ansdict):
    checkdict = question.getcheckdict()
    ans = ansdict['ANSWER'] or ''
    qtype = question.get_type()
    if qtype.startswith('choice-yesno'):
        if ans not in ('yes', 'no', 'dontknow'):
            raise AnswerException(_(u'You must select an option'))
        if qtype == 'choice-yesnocomment' \
                and len(ansdict.get('comment', '').strip()) == 0:
            if checkdict.get('required', False):
                raise AnswerException(_(u'Field cannot be blank'))
            if checkdict.get('required-yes', False) and ans == 'yes':
                raise AnswerException(_(u'Field cannot be blank'))
            if checkdict.get('required-no', False) and ans == 'no':
                raise AnswerException(_(u'Field cannot be blank'))
    else:
        if not ans.strip() and checkdict.get('required', False):
            raise AnswerException(_(u'Field cannot be blank'))
    if 'comment' in ansdict and len(ansdict['comment']) > 0:
        return dumps([ans, [ansdict['comment']]])
    if ans:
        return dumps([ans])
    return dumps([])


add_type('open', 'Open Answer, single line [input]')
add_type('open-textfield', 'Open Answer, multi-line [textarea]')
add_type('choice-yesno', 'Yes/No Choice [radio]')
add_type('choice-yesnocomment',
         'Yes/No Choice with optional comment [radio, input]')
add_type('choice-yesnodontknow', 'Yes/No/Don\'t know Choice [radio]')


@answer_proc('comment')
def process_comment(question, answer):
    pass


add_type('comment', 'Comment Only')
