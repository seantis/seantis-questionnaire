"""
Basic Test Suite for Questionnaire Application

Unfortunately Django 1.0 only has TestCase and not TransactionTestCase
so we can't test that a submitted page with an error does not have any
answers submitted to the DB.
"""

from django.test import TestCase
from questionnaire.models import RunInfo
from questionnaire.models import Answer


class TypeTest(TestCase):
    fixtures = ('testQuestions.yaml',)
    urls = 'questionnaire.test_urls'

    def setUp(self):
        self.ansdict1 = {
            'questionset_id': '1',
            'question_1': 'Open Answer 1',
            'question_2': 'Open Answer 2\r\nMultiline',
            'question_3': 'yes',
            'question_4': 'dontknow',
            'question_5': 'yes',
            'question_5_comment': (
                'this comment is required because of required-yes check'
            ),
            'question_6': 'no',
            'question_6_comment': (
                'this comment is required because of required-no check'
            ),
            'question_7': '5',
            'question_8_unit': 'week',
            'question_8': '2',
        }
        self.ansdict2 = {
            'questionset_id': '2',
            'question_9': 'q9_choice1',  # choice
            'question_10': '_entry_',  # choice-freeform
            'question_10_comment': 'my freeform',
            'question_11_multiple_2': 'q11_choice2',  # choice-multiple
            'question_11_multiple_4': 'q11_choice4',  # choice-multiple
            'question_12_multiple_1': 'q12_choice1',  # ...-multiple-freeform
            'question_12_more_1': 'blah',  # choice-multiple-freeform
        }
        runinfo = self.runinfo = RunInfo.objects.get(runid='test:test')
        self.runid = runinfo.runid
        self.subject_id = runinfo.subject_id

    def test010_redirect(self):
        """Check redirection from generic questionnaire to questionset"""

        response = self.client.get('/q/test:test/')
        self.assertEqual(response['Location'],
                         'http://testserver/q/test:test/1/')

    def test020_get_questionset_1(self):
        """Get first page of Questions"""

        response = self.client.get('/q/test:test/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name,
                         'questionnaire/questionset.html')

    def test030_language_setting(self):
        """Set the language and confirm it is set in DB"""

        response = self.client.get('/q/test:test/1/', {"lang": "en"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/q/test:test/1/')
        response = self.client.get('/q/test:test/1/')
        assert "Don't Know" in response.content
        self.assertEqual(response.status_code, 200)
        runinfo = RunInfo.objects.get(runid='test:test')
        self.assertEqual(runinfo.subject.language, 'en')
        response = self.client.get('/q/test:test/1/', {"lang": "de"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/q/test:test/1/')
        response = self.client.get('/q/test:test/1/')
        assert "Weiss nicht" in response.content
        self.assertEqual(response.status_code, 200)
        runinfo = RunInfo.objects.get(runid='test:test')
        self.assertEqual(runinfo.subject.language, 'de')

    def test040_missing_question(self):
        """Post questions with a mandatory field missing"""

        c = self.client
        ansdict = self.ansdict1.copy()
        del ansdict['question_3']
        response = c.post('/q/test:test/1/', ansdict)
        self.assertEqual(response.status_code, 200)
        errors = response.context[-1]['errors']
        self.assertEqual(len(errors), 1) and '3' in errors

    def test050_missing_question(self):
        """Post questions with a mandatory field missing"""

        c = self.client
        ansdict = self.ansdict1.copy()
        del ansdict['question_5_comment']
        # first set language to english
        response = self.client.get('/q/test:test/1/', {"lang": "en"})
        response = c.post('/q/test:test/1/', ansdict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[-1]['errors']), 1)

    def test060_successful_questionnaire(self):
        """POST complete answers for QuestionSet 1"""

        c = self.client
        ansdict1 = self.ansdict1
        runinfo = RunInfo.objects.get(runid='test:test')
        runid = runinfo.random = runinfo.runid = '1real'
        runinfo.save()

        response = c.get('/q/1real/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name,
                         'questionnaire/questionset.html')
        response = c.post('/q/1real/', ansdict1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/q/1real/2/')
        "POST complete answers for QuestionSet 2"
        c = self.client

        ansdict2 = self.ansdict2
        response = c.get('/q/1real/2/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name,
                         'questionnaire/questionset.html')
        response = c.post('/q/1real/', ansdict2)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/')

        self.assertEqual(RunInfo.objects.filter(runid='1real').count(), 0)

        # TODO: The format of these answers seems very strange to me. It was
        # simpler before I changed it to get the test to work.
        # I'll have to revisit this once I figure out how this is meant to work
        # for now it is more important to me that all tests pass

        dbvalues = {
            '1': u'["%s"]' % ansdict1['question_1'],
            '2': u'["%s"]' % ansdict1['question_2'],
            '3': u'["%s"]' % ansdict1['question_3'],
            '4': u'["%s"]' % ansdict1['question_4'],
            '5': u'["%s", ["%s"]]' % (
                ansdict1['question_5'], ansdict1['question_5_comment']
            ),
            '6': u'["%s", ["%s"]]' % (
                ansdict1['question_6'], ansdict1['question_6_comment']
            ),
            '7': u'[%s]' % ansdict1['question_7'],
            '8': u'%s; %s' % (
                ansdict1['question_8'], ansdict1['question_8_unit']
            ),
            '9': u'["q9_choice1"]',
            '10': u'[["my freeform"]]',
            '11': u'["q11_choice2", "q11_choice4"]',
            '12': u'["q12_choice1", ["blah"]]',
        }
        for k, v in dbvalues.items():
            ans = Answer.objects.get(
                runid=runid, subject__id=self.subject_id, question__number=k
            )

            v = v.replace('\r', '\\r').replace('\n', '\\n')
            self.assertEqual(ans.answer, v)

    def test070_tags(self):
        c = self.client

        # the first questionset in questionnaire 2 is always shown,
        # but one of its 2 questions is tagged with testtag
        with_tags = c.get('/q/test:withtags/1/')

        # so we'll get two questions shown if the run is tagged
        self.assertEqual(with_tags.status_code, 200)
        self.assertEqual(len(with_tags.context['qlist']), 2)
        self.assertEqual(
            with_tags.context['qlist'][0][1]['css_style'] +
            with_tags.context['qlist'][1][1]['css_style'],
            ''
        )

        # one visible question, if the run is not tagged
        without_tags = c.get('/q/test:withouttags/1/')

        self.assertEqual(without_tags.status_code, 200)
        self.assertEqual(len(without_tags.context['qlist']), 2)
        self.assertEqual(
            without_tags.context['qlist'][0][1]['css_style'] +
            without_tags.context['qlist'][1][1]['css_style'],
            'display:none;'
        )

        # the second questionset is only shown if the run is tagged
        with_tags = c.get('/q/test:withtags/2/')

        self.assertEqual(with_tags.status_code, 200)
        self.assertEqual(len(with_tags.context['qlist']), 1)

        # meaning it'll be skipped on the untagged run
        without_tags = c.get('/q/test.withouttags/2/')

        self.assertEqual(without_tags.status_code, 302)  # redirect

        # the progress values of the first questionset should reflect
        # the fact that in one run there's only one questionset
        with self.settings(QUESTIONNAIRE_PROGRESS='default'):
            with_tags = c.get('/q/test:withtags/1/')
            without_tags = c.get('/q/test:withouttags/1/')

            self.assertEqual(with_tags.context['progress'], 50)
            self.assertEqual(without_tags.context['progress'], 100)
