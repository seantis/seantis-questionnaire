#!/usr/bin/python
# vim: set fileencoding=utf-8

from django.http import HttpResponse, Http404, \
    HttpResponsePermanentRedirect, HttpResponseRedirect
from django.template import RequestContext, Context, Template, loader
from django.views.decorators.cache import cache_control
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.sites.models import Site
from django.db import transaction
from django.conf import settings
from models import *
from questionnaire import QuestionProcessors, Processors, AnswerException, \
    questionset_done, questionnaire_done
from datetime import datetime
from django.utils import translation
import time, os, smtplib, rfc822
from parsers import *
from utils import numal_sort, split_numal, calc_alignment
from emails import send_emails, _send_email
import logging


def r2r(tpl, request, **contextdict):
    "Shortcut to use RequestContext instead of Context in templates"
    contextdict['request'] = request
    return render_to_response(tpl, contextdict, context_instance = RequestContext(request))


def get_runinfo(random):
    "Return the RunInfo entry with the provided random key"
    res = RunInfo.objects.filter(random=random.lower())
    if res:
        return res[0]
    return None


def get_question(number, questionnaire):
    "Return the specified Question (by number) from the specified Questionnaire"
    res = Question.objects.filter(number=number, questionset__questionnaire=questionnaire)
    if res:
        return res[0]
    return None


def delete_answer(question, subject, runid):
    "Delete the specified question/subject/runid combination from the Answer table"
    Answer.objects.filter(subject=subject, runid=runid, question=question).delete()


def add_answer(runinfo, question, answer_dict):
    """
    Add an Answer to a Question for RunInfo, given the relevant form input
    
    answer_dict contains the POST'd elements for this question, minus the
    question_{number} prefix.  The question_{number} form value is accessible
    with the ANSWER key.
    """
    answer = Answer()
    answer.question = question
    answer.subject = runinfo.subject
    answer.runid = runinfo.runid

    type = question.get_type()

    if "ANSWER" not in answer_dict:
        answer_dict['ANSWER'] = None

    if type in Processors:
        answer.answer = Processors[type](question, answer_dict) or ''
    else:
        raise AnswerException("No Processor defined for question type %s" % type)

    # first, delete all existing answers to this question for this particular user+run
    delete_answer(question, runinfo.subject, runinfo.runid)
    # then save the new answer to the database
    answer.save()
    return True


def questionset_satisfies_checks(questionset, runinfo):
    "Return True is RunInfo satisfied checks for the specified QuestionSet"
    checks = parse_checks(questionset.checks)
    for check, value in checks.items():
        if check == 'maleonly' and runinfo.subject.gender != 'male':
            return False
        if check == 'femaleonly' and runinfo.subject.gender != 'female':
            return False
        if check == 'shownif' and value and value.strip():
            depparser = BooleanParser(dep_check, runinfo, {})
            res = depparser.parse(value)
            if not res:
                return False
    return True


def redirect_to_qs(runinfo):
    "Redirect to the correct and current questionset URL for this RunInfo"
    url = reverse("questionset",
                args=[ runinfo.random, runinfo.questionset.sortid ])
    return HttpResponseRedirect(url)


@transaction.commit_on_success
def questionnaire(request, runcode=None, qs=None):
    """
    Process submitted answers (if present) and redirect to next page

    If this is a POST request, parse the submitted data in order to store
    all the submitted answers.  Then return to the next questionset or
    return a completed response.

    If this isn't a POST request, redirect to the main page.

    We only commit on success, to maintain consistency.  We also specifically
    rollback if there were errors processing the answers for this questionset.
    """

    # if runcode provided as query string, redirect to the proper page
    if not runcode:
        if not request.GET.get('runcode', None):
            return HttpResponseRedirect("/")
        return HttpResponseRedirect(
            reverse("questionnaire",
                args=[request.GET['runcode']]))

    runinfo = get_runinfo(runcode)

    if not runinfo:
        transaction.commit()
        return HttpResponseRedirect('/')

    if not qs:
        # Only change the language to the subjects choice for the initial
        # questionnaire page (may be a direct link from an email)
        if hasattr(request, 'session'):
            request.session['django_language'] = runinfo.subject.language
            translation.activate(runinfo.subject.language)

    if 'lang' in request.GET:
        return set_language(request, runinfo, request.path)

    # --------------------------------
    # --- Handle non-POST requests --- 
    # --------------------------------

    if request.method != "POST":
        if qs is not None:
            qs = get_object_or_404(QuestionSet, sortid=qs, questionnaire=runinfo.questionset.questionnaire)
            if runinfo.random.startswith('test:'):
                pass # ok for testing
            elif qs.sortid > runinfo.questionset.sortid:
                # you may jump back, but not forwards
                return redirect_to_qs(runinfo)
            runinfo.questionset = qs
            runinfo.save()
            transaction.commit()
        # no questionset id in URL, so redirect to the correct URL
        if qs is None:
            return redirect_to_qs(runinfo)
        return show_questionnaire(request, runinfo)

    # -------------------------------------
    # --- Process POST with QuestionSet ---
    # -------------------------------------

    # if the submitted page is different to what runinfo says, update runinfo
    # XXX - do we really want this?
    qs = request.POST.get('questionset_id', None)
    try:
        qsobj = QuestionSet.objects.filter(pk=qs)[0]
        if qsobj.questionnaire == runinfo.questionset.questionnaire:
            if runinfo.questionset != qsobj:
                runinfo.questionset = qsobj
                runinfo.save()
    except:
        pass

    questionnaire = runinfo.questionset.questionnaire
    questionset = runinfo.questionset

    # to confirm that we have the correct answers
    expected = questionset.questions()

    items = request.POST.items()
    extra = {} # question_object => { "ANSWER" : "123", ... }

    # this will ensure that each question will be processed, even if we did not receive
    # any fields for it. Also works to ensure the user doesn't add extra fields in
    for x in expected:
        items.append( (u'question_%s_Trigger953' % x.number, None) )

    # generate the answer_dict for each question, and place in extra
    for item in items:
        key, value = item[0], item[1]
        if key.startswith('question_'):
            answer = key.split("_", 2)
            question = get_question(answer[1], questionnaire)
            if not question:
                logging.warn("Unknown question when processing: %s" % answer[1])
                continue
            extra[question] = ans = extra.get(question, {})
            if(len(answer) == 2):
                ans['ANSWER'] = value
            elif(len(answer) == 3):
                ans[answer[2]] = value
            else:
                logging.warn("Poorly formed form element name: %r" % answer)
                continue
            extra[question] = ans

    errors = {}
    for question, ans in extra.items():
        if u"Trigger953" not in ans:
            logging.warn("User attempted to insert extra question (or it's a bug)")
            continue
        try:
            cd = question.getcheckdict()
            # requiredif is the new way
            depon = cd.get('requiredif',None) or cd.get('dependent',None)
            if depon:
                depparser = BooleanParser(dep_check, runinfo, extra)
                if not depparser.parse(depon):
                    # if check is not the same as answer, then we don't care
                    # about this question plus we should delete it from the DB
                    delete_answer(question, runinfo.subject, runinfo.runid)
                    if cd.get('store', False):
                        runinfo.set_cookie(question.number, None)
                    continue
            add_answer(runinfo, question, ans)
            if cd.get('store', False):
                runinfo.set_cookie(question.number, ans['ANSWER'])
        except AnswerException, e:
            errors[question.number] = e
        except Exception:
            logging.exception("Unexpected Exception")
            transaction.rollback()
            raise

    if len(errors) > 0:
        res = show_questionnaire(request, runinfo, errors=errors)
        transaction.rollback()
        return res

    questionset_done.send(sender=None,runinfo=runinfo,questionset=questionset)

    next = questionset.next()
    while next and not questionset_satisfies_checks(next, runinfo):
        next = next.next()
    runinfo.questionset = next
    runinfo.save()

    if next is None: # we are finished
        hist = RunInfoHistory()
        hist.subject = runinfo.subject
        hist.runid = runinfo.runid
        hist.completed = datetime.now()
        hist.save()

        questionnaire_done.send(sender=None, runinfo=runinfo,
                                questionnaire=questionnaire)

        redirect_url = questionnaire.redirect_url
        for x,y in (('$LANG', translation.get_language()),
                    ('$SUBJECTID', runinfo.subject.id),
                    ('$RUNID', runinfo.runid),):
            redirect_url = redirect_url.replace(x, str(y))

        if runinfo.runid in ('12345', '54321') \
        or runinfo.runid.startswith('test:'):
            runinfo.questionset = QuestionSet.objects.filter(questionnaire=questionnaire).order_by('sortid')[0]
            runinfo.save()
        else:
            runinfo.delete()
        transaction.commit()
        if redirect_url:
            return HttpResponseRedirect(redirect_url)
        return r2r("questionnaire/complete.$LANG.html", request)

    transaction.commit()
    return redirect_to_qs(runinfo)


def get_progress(percent):
    "Based on a percentage as a float, calculate percentage needed for CSS progress bar"
    if int(percent) >= 1:
        return 100, "1"
    pc = "-%s" % (120 - int(percent * 120) + 1)
    return (int(percent * 100), pc)


def show_questionnaire(request, runinfo, errors={}):
    """
    Return the QuestionSet template

    Also add the javascript dependency code.
    """
    questions = runinfo.questionset.questions()
    total = len(runinfo.questionset.questionnaire.questionsets())

    qlist = []
    jsinclude = []      # js files to include
    cssinclude = []     # css files to include
    jstriggers = []
    qvalues = {}
    alignment=4
    for question in questions:
        Type = question.get_type()
        _qnum, _qalpha = split_numal(question.number)
        if _qalpha:
            _qalpha_class = ord(_qalpha[-1]) % 2 and 'odd' or 'even'
        qdict = {
            'template' : 'questionnaire/%s.html' % (Type),
            'qnum' : _qnum,
            'qalpha' : _qalpha,
            'qtype' : Type,
            'qnum_class' : (_qnum % 2 == 0) and " qeven" or " qodd",
            'qalpha_class' : _qalpha and (ord(_qalpha[-1]) % 2 \
                                          and ' alodd' or ' aleven') or '',
        }

        if not question.newline():
            alignment = max(alignment, calc_alignment(question.text))

        # add javascript dependency checks
        cd = question.getcheckdict()
        depon = cd.get('requiredif',None) or cd.get('dependent',None)
        if depon:
            # extra args to BooleanParser are not required for toString
            parser = BooleanParser(dep_check)
            qdict['checkstring'] = ' checks="%s"' % parser.toString(depon)
            jstriggers.append('qc_%s' % question.number)
        if 'default' in cd:
            qvalues[question.number] = cd['default']
        if Type in QuestionProcessors:
            qdict.update(QuestionProcessors[Type](request, question))
            if 'alignment' in qdict:
                alignment = max(alignment, qdict['alignment'])
            if 'jsinclude' in qdict:
                if qdict['jsinclude'] not in jsinclude:
                    jsinclude.extend(qdict['jsinclude'])
            if 'cssinclude' in qdict:
                if qdict['cssinclude'] not in cssinclude:
                    cssinclude.extend(qdict['jsinclude'])
            if 'jstriggers' in qdict:
                jstriggers.extend(qdict['jstriggers'])
            if 'qvalue' in qdict:
                qvalues[question.number] = qdict['qvalue']
        qlist.append( (question, qdict) )

    progress = None
    if runinfo.questionset.sortid != 0:
        progress = get_progress(runinfo.questionset.sortid / float(total))

    # initialize qvalues
    for k,v in runinfo.get_cookiedict().items():
        qvalues[k] = v
    if request.POST:
        for k,v in request.POST.items():
            if k.startswith("question_"):
                s = k.split("_")
                if len(s) == 2:
                    qvalues[s[1]] = v

    r = r2r("questionnaire/questionset.html", request,
        questionset=runinfo.questionset,
        runinfo=runinfo,
        errors=errors,
        qlist=qlist,
        progress=progress,
        triggers=jstriggers,
        qvalues=qvalues,
        alignment=alignment,
        jsinclude=jsinclude,
        cssinclude=cssinclude)
    r['Cache-Control'] = 'no-cache'
    r['Expires'] = "Thu, 24 Jan 1980 00:00:00 GMT"
    return r


def set_language(request, runinfo=None, next=None):
    """
    Change the language, save it to runinfo if provided, and
    redirect to the provided URL (or the last URL).
    Can also be used by a url handler, w/o runinfo & next.
    """
    if not next:
        next = request.REQUEST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
        if not next:
            next = '/'
    response = HttpResponseRedirect(next)
    response['Expires'] = "Thu, 24 Jan 1980 00:00:00 GMT"
    if request.method == 'GET':
        lang_code = request.GET.get('lang', None)
        if lang_code and translation.check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
            if runinfo:
                runinfo.subject.language = lang_code
                runinfo.subject.save()
    return response


@permission_required("questionnaire.export")
def export_csv(request, qid): # questionnaire_id
    """
    For a given questionnaire id, generaete a CSV containing all the
    answers for all subjects.
    """
    import tempfile, csv
    from django.core.servers.basehttp import FileWrapper

    fd = tempfile.TemporaryFile()
    qid = int(qid)
    columns = [x[0] for x in Question.objects.filter(questionset__questionnaire__id = qid).distinct('number').values_list('number')]
    columns.sort(numal_sort)
    columns.insert(0,u'subject')
    columns.insert(1,u'runid')
    writer = csv.DictWriter(fd, columns, restval='--')
    coldict = {}
    for col in columns:
        coldict[col] = col
    writer.writerows([coldict,])
    answers = Answer.objects.filter(question__questionset__questionnaire__id = qid).order_by('subject', 'runid', 'question__number',)
    if not answers:
        raise Exception, "EMPTY!" # FIXME

    runid = answers[0].runid
    subject = answers[0].subject
    d = { u'subject' : "%s/%s" % (subject.id, subject.state), u'runid' : runid }
    for answer in answers:
        if answer.runid != runid or answer.subject != subject:
            writer.writerows([d,])
            runid = answer.runid
            subject = answer.subject
            d = { u'subject' : "%s/%s" % (subject.id, subject.state), u'runid' : runid }
        d[answer.question.number] = answer.answer.encode('utf-8')
    # and don't forget about the last one
    if d:
        writer.writerows([d,])
    response = HttpResponse(FileWrapper(fd), mimetype="text/csv")
    response['Content-Length'] = fd.tell()
    response['Content-Disposition'] = 'attachment; filename="export-%s.csv"' % qid
    fd.seek(0)
    return response


def dep_check(expr, runinfo, answerdict):
    """
    Given a comma separated question number and expression, determine if the
    provided answer to the question number satisfies the expression.

    If the expression starts with >, >=, <, or <=, compare the rest of
    the expression numerically and return False if it's not able to be
    converted to an integer.

    If the expression starts with !, return true if the rest of the expression
    does not match the answer.

    Otherwise return true if the expression matches the answer.

    If there is no comma and only a question number, it checks if the answer
    is "yes"

    When looking up the answer, it first checks if it's in the answerdict,
    then it checks runinfo's cookies, then it does a database lookup to find
    the answer.
    
    The use of the comma separator is purely historical.
    """
    questionnaire = runinfo.questionset.questionnaire
    if "," not in expr:
        expr = expr + ",yes"
    check_questionnum, check_answer = expr.split(",",1)
    try:
        check_question = Question.objects.get(number=check_questionnum,
          questionset__questionnaire = questionnaire)
    except Question.DoesNotExist:
        return False
    if check_question in answerdict:
        actual_answer = answerdict[check_question].get('ANSWER', '')
    elif runinfo.get_cookie(check_questionnum, False):
        actual_answer = runinfo.get_cookie(check_questionnum)
    else:
        # retrieve from database
        logging.warn("Put `store` in checks field for question %s" \
            % check_questionnum)
        ansobj = Answer.objects.filter(question=check_question,
            runid=runinfo.runid, subject=runinfo.subject)
        if ansobj:
            actual_answer = ansobj[0].answer.split(";")[0]
        else:
            actual_answer = None
    if actual_answer is None:
        actual_answer = u''
    if check_answer[0:1] in "<>":
        try:
            actual_answer = float(actual_answer)
            if check_answer[1:2] == "=":
                check_value = float(check_answer[2:])
            else:
                check_value = float(check_answer[1:])
        except:
            logging.error("ERROR: must use numeric values with < <= => > checks (%r)" % check_question)
            return False
        if check_answer.startswith("<="):
            return actual_answer <= check_value
        if check_answer.startswith(">="):
            return actual_answer >= check_value
        if check_answer.startswith("<"):
            return actual_answer < check_value
        if check_answer.startswith(">"):
            return actual_answer > check_value
    if check_answer.startswith("!"):
        return check_answer[1:].strip() != actual_answer.strip()
    return check_answer.strip() == actual_answer.strip()

@permission_required("questionnaire.management")
def send_email(request, runinfo_id):
    if request.method != "POST":
        return HttpResponse("This page MUST be called as a POST request.")
    runinfo = get_object_or_404(RunInfo, pk=int(runinfo_id))
    successful = _send_email(runinfo)
    return r2r("emailsent.html", request, runinfo=runinfo, successful=successful)
