# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django import http
from django.utils import translation
from models import Page

def page(request, page):
    p = get_object_or_404(Page, slug=page)
    if not p.public:
        raise Http404
    return render_to_response("page.html", { "request" : request, "page":p, }, context_instance = RequestContext(request) )

def langpage(request, lang, page):
    translation.activate_language(lang)
    return page(request, page)

def set_language(request):
    next = request.REQUEST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
        if not next:
            next = '/'
    response = http.HttpResponseRedirect(next)
    if request.method == 'GET':
        lang_code = request.GET.get('language', None)
        if lang_code and translation.check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response

