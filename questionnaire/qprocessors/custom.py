#
# Custom type exists for backwards compatibility. All custom types should now
# exist in the drop down list of the management interface.
#
from django.utils.translation import ugettext as _

from questionnaire import add_type
from questionnaire import answer_proc
from questionnaire import AnswerException
from questionnaire import Processors
from questionnaire import question_proc
from questionnaire import QuestionProcessors


@question_proc('custom')
def question_custom(request, question):
    cd = question.getcheckdict()
    _type = cd['type']
    d = {}
    if _type in QuestionProcessors:
        d = QuestionProcessors[_type](request, question)
    if 'template' not in d:
        d['template'] = 'questionnaire/%s.html' % _type
    return d


@answer_proc('custom')
def process_custom(question, answer):
    cd = question.getcheckdict()
    _type = cd['type']
    if _type in Processors:
        return Processors[_type](question, answer)
    raise AnswerException(_(u"Processor not defined for this question"))


add_type('custom', 'Custom field')
