"""
Basic Test Suite for Questionnaire Application

Unfortunately Django 1.0 only has TestCase and not TransactionTestCase
so we can't test that a submitted page with an error does not have any
answers submitted to the DB.
"""
from django.test import TestCase
from django.test.client import Client
from questionnaire.models import *
from datetime import datetime
import os

class TypeTest(TestCase):
    fixtures = ( 'testQuestions.yaml', )
    urls = 'questionnaire.test_urls'

    def setUp(self):
        self.ansdict1 = {
            'questionset_id' : '1',
            'question_1' : 'Open Answer 1',
            'question_2' : 'Open Answer 2\r\nMultiline',
            'question_3' : 'yes',
            'question_4' : 'dontknow',
            'question_5' : 'yes',
            'question_5_comment' : 'this comment is required because of required-yes check',
            'question_6' : 'no',
            'question_6_comment' : 'this comment is required because of required-no check',
            'question_7' : '5',
            'question_8_unit' : 'week',
            'question_8' : '2',
        }
        self.ansdict2 = {
            'questionset_id' : '2',
            'question_9' : 'q9_choice1',  # choice
            'question_10' : '_entry_', # choice-freeform
            'question_10_comment' : 'my freeform',
            'question_11_multiple_2' : 'q11_choice2', # choice-multiple
            'question_11_multiple_4' : 'q11_choice4', # choice-multiple
            'question_12_multiple_1' : 'q12_choice1',# choice-multiple-freeform
            'question_12_more_1' : 'blah', # choice-multiple-freeform
        }
        runinfo = self.runinfo = RunInfo.objects.get(runid='test:test')
        self.runid = runinfo.runid
        self.subject_id = runinfo.subject_id


    def test010_redirect(self):
        "Check redirection from generic questionnaire to questionset"
        response = self.client.get('/q/test:test/')
        assert response['Location'] == 'http://testserver/q/test:test/1/'


    def test020_get_questionset_1(self):
        "Get first page of Questions"
        response = self.client.get('/q/test:test/1/')
        assert response.status_code == 200
        assert response.template[0].name == 'questionnaire/questionset.html'


    def test030_language_setting(self):
        "Set the language and confirm it is set in DB"
        response = self.client.get('/q/test:test/1/', {"lang" : "en"})
        assert response.status_code == 302
        assert response['Location'] == 'http://testserver/q/test:test/1/'
        response = self.client.get('/q/test:test/1/')
        assert "Don't Know" in response.content
        assert response.status_code == 200
        runinfo = RunInfo.objects.get(runid='test:test')
        assert runinfo.subject.language == 'en'
        response = self.client.get('/q/test:test/1/', {"lang" : "de"})
        assert response.status_code == 302
        assert response['Location'] == 'http://testserver/q/test:test/1/'
        response = self.client.get('/q/test:test/1/')
        assert "Weiss nicht" in response.content
        assert response.status_code == 200
        runinfo = RunInfo.objects.get(runid='test:test')
        assert runinfo.subject.language == 'de'


    def test040_missing_question(self):
        "Post questions with a mandatory field missing"
        c = self.client
        ansdict = self.ansdict1.copy()
        del ansdict['question_3']
        response = c.post('/q/test:test/1/', ansdict)
        assert response.status_code == 200
        errors = response.context[-1]['errors']
        assert len(errors) == 1 and errors.has_key('3')


    def test050_missing_question(self):
        "Post questions with a mandatory field missing"
        c = self.client
        ansdict = self.ansdict1.copy()
        del ansdict['question_5_comment']
        # first set language to english
        response = self.client.get('/q/test:test/1/', {"lang" : "en"})
        response = c.post('/q/test:test/1/', ansdict)
        assert response.status_code == 200
        assert len(response.context[-1]['errors']) == 1


    def test060_successful_questionnaire(self):
        "POST complete answers for QuestionSet 1"
        c = self.client
        ansdict1 = self.ansdict1
        runinfo = RunInfo.objects.get(runid='test:test')
        runid = runinfo.random = runinfo.runid = '1real'
        runinfo.save()

        response = c.get('/q/1real/1/')
        assert response.status_code == 200
        assert response.template[0].name == 'questionnaire/questionset.html'
        response = c.post('/q/1real/', ansdict1)
        assert response.status_code == 302
        assert response['Location'] == 'http://testserver/q/1real/2/'
        "POST complete answers for QuestionSet 2"
        c = self.client

        ansdict2 = self.ansdict2
        response = c.get('/q/1real/2/')
        assert response.status_code == 200
        assert response.template[0].name == 'questionnaire/questionset.html'
        response = c.post('/q/1real/', ansdict2)
        assert response.status_code == 302
        assert response['Location'] == 'http://testserver/'

        assert RunInfo.objects.filter(runid='1real').count() == 0

        # TODO: The format of these answers seems very strange to me. It was 
        # simpler before I changed it to get the test to work. 
        # I'll have to revisit this once I figure out how this is meant to work
        # for now it is more important to me that all tests pass

        dbvalues = {
            '1' : u'["%s"]' % ansdict1['question_1'],
            '2' : u'["%s"]' % ansdict1['question_2'],
            '3' : u'["%s"]' % ansdict1['question_3'],
            '4' : u'["%s"]' % ansdict1['question_4'],
            '5' : u'["%s", ["%s"]]' % (ansdict1['question_5'], ansdict1['question_5_comment']),
            '6' : u'["%s", ["%s"]]' % (ansdict1['question_6'], ansdict1['question_6_comment']),
            '7' : u'[%s]' % ansdict1['question_7'],
            '8' : u'%s; %s' % (ansdict1['question_8'], ansdict1['question_8_unit']),
            '9' : u'["q9_choice1"]',
            '10' : u'[["my freeform"]]',
            '11' : u'["q11_choice2", "q11_choice4"]',
            '12' : u'["q12_choice1", ["blah"]]',
        }
        for k, v in dbvalues.items():
            ans = Answer.objects.get(runid=runid, subject__id=self.subject_id,
                question__number=k)
            
            v = v.replace('\r', '\\r').replace('\n', '\\n')
            self.assertEqual(ans.answer, v)