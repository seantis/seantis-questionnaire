Changes
=======

As of november 2011 this app is being developed more actively again by Seantis
GmbH. The goal is to clean it up, modernize and document it as we are working
to include it in a new project.

This means we will break some backwards compatibility, mainly on the front end
as the HTML code is being moved from using blueprint to using Twitter bootstrap.

As a result it's not advisable for current users to upgrade existing questionnaires
to the current development tip as it might break things. 

So far the format of the questionsets has not changed, so they could still be 
reused, but the style and structure of the output has changed significantly and 
existing sites cannot expect to look the same after an upgrade.

For existing users two tags in the repository are of interest:

 * tag 1.0 - state of last commit by the original developer (rmt)
 * tag 1.1 - contains merged changes by other forks improving the orignal

Better documentation and an example site for the updated questionnaire will be 
available within the next couple of weeks...months. 


About Seantis Questionnaire
===========================

Seantis Questionnaire is a django questionnaire app which is easily customised
and includes advanced dependency support using boolean expressions.

It allows an administrator to create and edit questionnaires in the django
admin interface, with support for multiple languages.

It was originally created to support an annually recurring questionnnaire for a
medical study.

This repository only contains the Questionnaire side of the application.  We
also developed a management interface and extensions to the models that are
specific to the study, and have therefore not been made public.  Seantis GmbH
could, however, provide a similar end-to-end solution for your organisation.


Alternatives
============

There are two other questionnaire-type applications that I stumbled upon, but
they both didn't quite scratch my itch, but they may scratch yours.

Django Questionnaire - http://djangoquest.aperte-it.com/

Django Survey - http://code.google.com/p/django-survey/


Requirements
============

Seantis Questionnaire has some external dependencies that you must
install.

django-transmeta - used for simple internationalisation
    http://code.google.com/p/django-transmeta/source/checkout

pyparsing - used for the boolean dependency parser
    http://pyparsing.wikispaces.com/Download+and+Installation
    $ easy_install pyparsing

textile - used for marking up the questions
    $ easy_install textile

