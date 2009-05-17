"""
Functions to send email reminders to users.
"""

from django.core.mail import SMTPConnection, EmailMessage
from django.contrib.auth.decorators import login_required
from django.template import Context, loader
from django.utils import translation
from django.conf import settings
from models import Subject, QuestionSet, RunInfo
from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404
import random, time, smtplib, rfc822
try: from hashlib import md5
except: from md5 import md5


class SmarterEmailMessage(EmailMessage):
    """
    SmarterEmailMessage allows rfc822 valid To addresses
    """
    def recipients(self):
        """
        For all recipients, convert to plain email address.
        ie. Given "Joe Bloggs "<joe@example.com>, return joe@example.com
        """
        return map(lambda x: rfc822.parseaddr(x)[1], self.to + self.bcc)


def _new_random(subject):
    """
    Create a short unique randomized string.
    Returns: subject_id + 'z' +
        md5 hexdigest of subject's surname, nextrun date, and a random number
    """
    return "%dz%s" % (subject.id, md5(subject.surname + str(subject.nextrun) + hex(random.randint(1,999999))).hexdigest()[:6])


def _new_runinfo(subject, questionset):
    """
    Create a new RunInfo entry with a random code

    If a unique subject+runid entry already exists, return that instead..
    That should only occurs with manual database changes
    """
    nextrun = subject.nextrun
    runid = str(nextrun.year)
    entries = list(RunInfo.objects.filter(runid=runid, subject=subject))
    if len(entries)>0:
        r = entries[0]
    else:
        r = RunInfo()
        r.random = _new_random(subject)
        r.subject = subject
        r.runid = runid
        r.emailcount = 0
        r.created = datetime.now()
    r.questionset = questionset
    r.save()
    if nextrun.month == 2 and nextrun.day == 29: # the only exception?
        subject.nextrun = datetime(nextrun.year + 1, 2, 28)
    else:
        subject.nextrun = datetime(nextrun.year + 1, nextrun.month, nextrun.day)
    subject.save()
    return r

def _send_email(runinfo):
    "Send the email for a specific runinfo entry"
    subject = runinfo.subject
    translation.activate(subject.language)
    tmpl = loader.get_template(settings.QUESTIONNAIRE_EMAIL_TEMPLATE)
    c = Context()
    c['surname'] = subject.surname
    c['givenname'] = subject.givenname
    c['gender'] = subject.gender
    c['email'] = subject.email
    c['random'] = runinfo.random
    c['runid'] = runinfo.runid
    c['created'] = runinfo.created
    c['site'] = getattr(settings, 'QUESTIONNAIRE_URL', '(settings.QUESTIONNAIRE_URL not set)')
    email = tmpl.render(c)
    emailFrom = settings.QUESTIONNAIRE_EMAIL_FROM
    emailSubject, email = email.split("\n",1) # subject must be on first line
    emailSubject = emailSubject.strip()
    emailFrom = emailFrom.replace("$RUNINFO", runinfo.random)
    emailTo = '"%s, %s" <%s>' % (subject.surname, subject.givenname, subject.email)

    try:
        conn = SMTPConnection()
        msg = SmarterEmailMessage(emailSubject, email, emailFrom, [ emailTo ],
                                  connection=conn)
        msg.send()
        runinfo.emailcount = 1 + runinfo.emailcount
        runinfo.emailsent = datetime.now()
        runinfo.lastemailerror = "OK, accepted by server"
        runinfo.save()
        return True
    except smtplib.SMTPRecipientsRefused:
        runinfo.lastemailerror = "SMTP Recipient Refused"
    except smtplib.SMTPHeloError:
        runinfo.lastemailerror = "SMTP Helo Error"
    except smtplib.SMTPSenderRefused:
        runinfo.lastemailerror = "SMTP Sender Refused"
    except smtplib.SMTPDataError:
        runinfo.lastemailerror = "SMTP Data Error"
    runinfo.save()
    return False


def send_emails(request=None, qname=None):
    """
    1. Create a runinfo entry for each subject who is due and has state 'active'
    2. Send an email for each runinfo entry whose subject receives email,
       providing that the last sent email was sent more than a week ago.

    This can be called either by "./manage.py questionnaire_emails" (without
    request) or through the web, if settings.EMAILCODE is set and matches.
    """
    if request and request.GET.get('code') != getattr(settings,'EMAILCODE', False):
        raise Http404
    if not qname:
        qname = getattr(settings, 'QUESTIONNAIRE_DEFAULT', None)
    if not qname:
        raise Exception("QUESTIONNAIRE_DEFAULT not in settings")
    questionset = QuestionSet.objects.filter(questionnaire__name=qname).order_by('sortid')
    if not questionset:
        raise Exception("No questionsets for questionnaire '%s' (in settings.py)" % qname)
        return
    questionset = questionset[0]

    viablesubjects = Subject.objects.filter(nextrun__lte = datetime.now(), state='active')
    for s in viablesubjects:
        r = _new_runinfo(s, questionset)
    runinfos = RunInfo.objects.filter(subject__formtype='email', questionset__questionnaire=questionset)
    WEEKAGO = time.time() - (60 * 60 * 24 * 7) # one week ago
    outlog = []
    for r in runinfos:
        if r.runid.startswith('test:'):
            continue
        if r.emailcount == -1:
            continue
        if r.emailcount == 0 or time.mktime(r.emailsent.timetuple()) < WEEKAGO:
            try:
                if _send_email(r):
                    outlog.append(u"[%s] %s, %s: OK" % (r.runid, r.subject.surname, r.subject.givenname))
                else:
                    outlog.append(u"[%s] %s, %s: %s" % (r.runid, r.subject.surname, r.subject.givenname, r.lastemailerror))
            except Exception, e:
                outlog.append("Exception: [%s] %s: %s" % (r.runid, r.subject.surname, str(e)))
    if request:
        return HttpResponse("Sent Questionnaire Emails:\n  "
            +"\n  ".join(outlog), mimetype="text/plain")
    return "\n".join(outlog)
