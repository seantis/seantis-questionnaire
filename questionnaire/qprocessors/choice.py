from questionnaire import *
from django.utils.translation import ugettext as _, ungettext
from django.utils.simplejson import dumps

@question_proc('choice', 'choice-freeform')
def question_choice(request, question):
    choices = []
    jstriggers = []

    cd = question.getcheckdict()
    key = "question_%s" % question.number
    key2 = "question_%s_comment" % question.number
    val = None
    if key in request.POST:
        val = request.POST[key]
    else:
        if 'default' in cd:
            val = cd['default']
    for choice in question.choices():
        choices.append( ( choice.value == val, choice, ) )

    if question.type == 'choice-freeform':
        jstriggers.append('%s_comment' % question.number)

    return {
        'choices'   : choices,
        'sel_entry' : val == '_entry_',
        'qvalue'    : val or '',
        'required'  : True,
        'nobreaks'  : cd.get("nobreaks", False),
        'comment'   : request.POST.get(key2, ""),
        'jstriggers': jstriggers,
    }

@answer_proc('choice', 'choice-freeform')
def process_choice(question, answer):
    opt = answer['ANSWER'] or ''
    if not opt:
        raise AnswerException(_(u'You must select an option'))
    if opt == '_entry_' and question.type == 'choice-freeform':
        opt = answer.get('comment','')
        if not opt:
            raise AnswerException(_(u'Field cannot be blank'))
        return dumps([[opt]])
    else:
        valid = [c.value for c in question.choices()]
        if opt not in valid:
            raise AnswerException(_(u'Invalid option!'))
    return dumps([opt])
add_type('choice', 'Choice [radio]')
add_type('choice-freeform', 'Choice with a freeform option [radio]')


@question_proc('choice-multiple', 'choice-multiple-freeform')
def template_multiple(request, question):
    key = "question_%s" % question.number
    choices = []
    counter = 0
    cd = question.getcheckdict()
    defaults = cd.get('default','').split(',')
    for choice in question.choices():
        counter += 1
        key = "question_%s_multiple_%d" % (question.number, choice.sortid)
        if key in request.POST or \
          (request.method == 'GET' and choice.value in defaults):
            choices.append( (choice, key, ' checked',) )
        else:
            choices.append( (choice, key, '',) )
    extracount = int(cd.get('extracount', 0))
    if not extracount and question.type == 'choice-multiple-freeform':
        extracount = 1
    extras = []
    for x in range(1, extracount+1):
        key = "question_%s_more%d" % (question.number, x)
        if key in request.POST:
            extras.append( (key, request.POST[key],) )
        else:
            extras.append( (key, '',) )
    return {
        "choices": choices,
        "extras": extras,
        "nobreaks" : cd.get("nobreaks", False),
        "template"  : "questionnaire/choice-multiple-freeform.html",
        "required" : cd.get("required", False) and cd.get("required") != "0",

    }

@answer_proc('choice-multiple', 'choice-multiple-freeform')
def process_multiple(question, answer):
    multiple = []
    multiple_freeform = []

    requiredcount = 0
    required = question.getcheckdict().get('required', 0)
    if required:
        try:
            requiredcount = int(required)
        except ValueError:
            requiredcount = 1
    if requiredcount and requiredcount > question.choices().count():
        requiredcount = question.choices().count()

    for k, v in answer.items():
        if k.startswith('multiple'):
            multiple.append(v)
        if k.startswith('more') and len(v.strip()) > 0:
            multiple_freeform.append(v)

    if len(multiple) + len(multiple_freeform) < requiredcount:
        raise AnswerException(ungettext(u"You must select at least %d option",
                                        u"You must select at least %d options",
                                        requiredcount) % requiredcount)
    multiple.sort()
    if multiple_freeform:
        multiple.append(multiple_freeform)
    return dumps(multiple)
add_type('choice-multiple', 'Multiple-Choice, Multiple-Answers [checkbox]')
add_type('choice-multiple-freeform', 'Multiple-Choice, Multiple-Answers, plus freeform [checkbox, input]')


