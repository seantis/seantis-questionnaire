from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',

    url(r'q/', include('questionnaire.urls')),

    url(r'^take/(?P<questionnaire_id>[0-9]+)/$',
        'questionnaire.views.generate_run'),
    url(r'^$', 'questionnaire.page.views.page',
        {'page_to_render': 'index'}),
    url(r'^(?P<lang>..)/(?P<page_to_trans>.*)\.html$',
        'questionnaire.page.views.langpage'),
    url(r'^(?P<page_to_render>.*)\.html$', 'questionnaire.page.views.page'),
    url(r'^setlang/$', 'questionnaire.views.set_language'),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
