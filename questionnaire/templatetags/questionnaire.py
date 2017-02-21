#!/usr/bin/python
from django import template
from django.core.urlresolvers import reverse

register = template.Library()


@register.filter(name="dictget")
def dictget(thedict, key):
    "{{ dictionary|dictget:variableholdingkey }}"
    return thedict.get(key, None)


@register.filter(name="spanclass")
def spanclass(string):
    l = 2 + len(string.strip()) // 6
    if l <= 4:
        return "span-4"
    if l <= 7:
        return "span-7"
    if l < 10:
        return "span-10"
    return "span-%d" % l


@register.filter(name="qtesturl")
def qtesturl(question):
    qset = question.questionset
    return reverse(
        "questionset",
        args=("test:%s" % qset.questionnaire.id, qset.sortid)
    )
