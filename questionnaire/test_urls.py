from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^q/(?P<runcode>[^/]+)/(?P<qs>\d+)/$',
        'questionnaire.views.questionnaire', name='questionset'),
    url(r'^q/([^/]+)/',
        'questionnaire.views.questionnaire', name='questionset'),
    url(r'^q/manage/csv/(\d+)/',
        'questionnaire.views.export_csv'),
    url(r'^q/manage/sendemail/(\d+)/$',
        'questionnaire.views.send_email'),
    url(r'^q/manage/manage/sendemails/$',
        'questionnaire.emails.send_emails'),
    url(r'^q/(?P<runcode>[^/]+)/progress/$',
        'questionnaire.views.get_async_progress', name='progress'),
)
