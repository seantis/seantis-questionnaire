from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    (r'q/', include('questionnaire.urls')),
    (r'^$', 'page.views.page', {'page' : 'index'}),
    (r'^(?P<page>.*)\.html$', 'page.views.page'),
    (r'^(?P<lang>..)/(?P<page>.*)\.html$', 'page.views.langpage'),

    (r'^setlang/$', 'page.views.set_language'),

    (r'^media/(.*)', 'django.views.static.serve',
        { 'document_root' : settings.MEDIA_ROOT }),

    (r'^admin/(.*)', admin.site.root),
)
