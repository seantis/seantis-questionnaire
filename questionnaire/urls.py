# vim: set fileencoding=utf-8

from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^$',
            questionnaire, name='questionnaire_noargs'),
    url(r'^csv/(?P<qid>\d+)/',
            export_csv, name='export_csv'),
    url(r'^(?P<runcode>[^/]+)/(?P<qs>\d+)/$',
            questionnaire, name='questionset'),
    url(r'^(?P<runcode>[^/]+)/',
            questionnaire, name='questionnaire'),
)
