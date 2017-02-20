
WARNING
=======

**Seantis Questionnaire is no longer being developed.**

Have a look at this fork: https://github.com/eldest-daughter/ed-questionnaire


Seantis Questionnaire
=====================

Introduction
------------

Seantis Questionnaire is a django questionnaire app which is easily customised and includes advanced dependency support using boolean expressions.

It allows an administrator to create and edit questionnaires in the django admin interface, with support for multiple languages.


About this Manual
-----------------

Seantis Questionnaire is not a very well documented app so far to say the least. This manual should give you a general idea of the layout and concepts of it, but it is not as comprehensive as it should be.

What it does cover is the following:

* **Settings** explains the available options in the `settings.py`.
* **Integration** talks lays out the steps needed to create a new Django page together with the questionnaire. The same steps can be used to integrate the questionnaire into an existing site (though you would be entering unpaved ways).
* **Conecpts** talks about the data model and the design of the application.

Settings
--------

### `QUESTIONNAIRE_PROGRESS`
Defines the progressbar behavior in the questionnaire the possible options are `default`, `async` and `none`:

- `default`: The progressbar will be rendered in each questionset together with the questions. This is a good choice for smaller questionnaires as the progressbar will always be up to date.
- `async`:The progressbar value is updated using ajax once the questions have been rendered. This approach is the right choice for bigger questionnaires which
result in a long time spent on updating the progressbar with each request. The progress calculation is by far the most time consuming method in bigger questionnaires as all questionsets and questions need to be parsed to decide if they play a role in the current run or not.
- `none`: Completely omits the progressbar. Good if you don't want one or if the questionnaire is so huge that even the ajax request takes too long.

### `QUESTIONNAIRE_USE_SESSION`
Defines how the questionnaire and questionset id are passed around. If `False`, the default value, the ids are part of the URLs and visible to the user answering the questions. If `True`, the ids are set in the session and the URL remains unchanged as the user goes through the steps of the question set.


Integration
-----------

This part of the docs will take you through the steps needed to create a questionnaire app from scratch. It should also be quite handy for the task of integrating the questionnaire into an existing site.

First, create a folder for your new site:

    mkdir site
    cd site

Create and activate a virtual environment so your python packages don't influence your system

    virtualenv .
    source bin/activate

Install Django

    pip install django==1.8.17

Create your Django site

    django-admin.py startproject mysite

Create a place for the questionnare

    cd mysite
    mkdir apps
    cd apps

Clone the questionnaire source

    git clone git@github.com:seantis/seantis-questionnaire.git

You should now have a seantis-questionnaire folder in your apps folder

    cd seantis-questionnaire

The next step is to install the questionnaire.

    python setup.py install

If you are working with seantis-questionnaire from your own fork you may want to use `python setup.py develop` instead, which will save you from running `python setup.py install` every time the questionnaire changes

Next up we'll have a look at configuring your basic questionnaire.

First, you want to setup the languages used in your questionnaire, by opening settings.py in your site's folder (the one with the subfoler apps/)

Open settings.py and add following lines, representing your languages of choice:

    LANGUAGES = (
        ('de', _('German')),
        ('en', _('English')),
    )

At the top of settings.py you should at this point add

    from django.utils.translation import ugettext_lazy as _

We will use that below for the setup of the folders

Also add the locale and request cache middleware to MIDDLEWARE_CLASSES

    'django.middleware.locale.LocaleMiddleware',
    'questionnaire.request_cache.RequestCacheMiddleware',


And finally, add the additional django packages (sites, markup, transmeta), questionnaire and your app to your INSTALLED_APPS

    'django.contrib.sites',
    'django_markup',
    'transmeta',
    'questionnaire',
    'questionnaire.page',
    'mysite'

To get the "sites" framework working you also need to add the following setting:

    SITE_ID = 1

Next up we want to edit the urls.py of your project to hookup the questionnaire views with your site's url configuration.

For an empty site with enabled admin interface you should end up with something like this:

    from django.conf.urls import include, url
    from django.contrib import admin


    admin.autodiscover()

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),

        # questionnaire urls
        url(r'q/', include('questionnaire.urls')),
        url(r'^take/(?P<questionnaire_id>[0-9]+)/$',
            'questionnaire.views.generate_run'),
        url(r'^$', 'questionnaire.page.views.page',
            {'page_to_render': 'index'}),
        url(r'^(?P<lang>..)/(?P<page_to_trans>.*)\.html$',
            'questionnaire.page.views.langpage'),
        url(r'^(?P<page_to_render>.*)\.html$',
            'questionnaire.page.views.page'),
        url(r'^setlang/$', 'questionnaire.views.set_language'),
    ]


For the questionnaire itself it is only necessary to have the urls below `# questionnaire urls

Having done that we can initialize our database. For this to work you must have setup your DATABASES in settings.py

    python manage.py syncdb

The questionnaire expectes a base.html template to be there, with certain stylesheets and blocks inside. Have a look at `./apps/seantis-questionnaire/example/templates/base.html`

For now you might want to just copy the base.html to your own template folder.

    cp -r apps/seantis-questionnaire/example/mysite/templates mysite/

Congratulations, you have setup the basics of the questionnaire! At this point this site doesn't really do anything, as there are no questionnaires defined.

To see an example questionnaire you can do the following (unfortunately, this will only work if you have both English and German defined as Languages in settings.py)

    python manage.py loaddata ./apps/seantis-questionnaire/example/fixtures/initial_data.yaml

You may then start your development server

    python manage.py runserver

And navigate your browser to `http://127.0.0.1:8000/`

Have a look at the example folder!

Concepts
--------

The Seantis Questionnaire sports the following tables, described in detail below.

* Subject
* RunInfo
* RunInfoHistory
* Question
* Choice
* QuestionSet
* Questionnaire
* Answer

### Subject

A subject is someone filling out a questionnaire.

Subjects are primarily useful in a study where the participants answer a questionnaire repeatedly. In this case a subject may be entered. Whoever is conducting the study (i.e. the person running the questionnaire app), may then periodically send emails inviting the subjects to fill out the questionnaire.

Sending Emails is covered in detail later.

Of course, not every questionnaire is part of a study. Sometimes you just want to find out what people regard as more awesome: pirates or ninjas*?

*(it's pirates!)

Though a poll would be a better choice for this example, one can find the answer to that question with Seantis Questionnaire by using an anonymous subject. The next chapter *Questionnaire* will talk about that in more detail.

### RunInfo

A runinfo refers to the currently active run of a subject.

A subject who is presently taking a questionnaire is considered to be on a run. The runinfo refers to that run and carries information about it.

The most important information associated with a runinfo is the subject, a random value that is used to generate the unique url to the questionnaire, the result of already answered questions and the progress.

Once a run is over it is deleted with some information being carried over to the RunInfoHistory.

Runs can be tagged by any number of comma separated tags. If tags are used, questions can be made to only show up if the given tag is part of the RunInfo.

### RunInfoHistory

The runinfo history is used to refer to a set of answers.

### Question

A question is anything you want to ask a subject. Since this is usually not limited to yes or no type questions there are a number of different types you can use:

* **choice-yesno** - Yes or No
* **choice-yesnocomment** - Yes or No with a chance to comment on the answer
* **choice-yesnodontknow** - Yes or No or Whaaa?
* **open** - A simple one line input box
* **open-textfield** - A box for lengthy answers
* **choice** - A list of choices to choose from
* **choice-freeform** - A list of choices with a chance to enter something else
* **choice-multiple** - A list of choices with multiple answers
* **choice-multiple-freeform** - Multiple Answers with multiple user defined answers
* **range** - A range of number from which one number can be chosen
* **number** - a number
* **timeperiod** - A timeperiod
* **custom** - custom question using a custom template
* **comment** - Not a question, but only a comment displayed to the user
* **sameas** - same type as some other question

*Some of these types, depend on checks or choices. The number question for instance can be controlled by setting the checks to something like "range=1-100 step=1". The range question may also use the before-mentioned checks and also "unit=%". Other questions like the choice-multiple-freeform need a "extracount=10" if ten extra options should be given to the user.

I would love to go into all the details here but time I have not so I my only choice is to kindly refer you to the qprocessor submodule which handles all the question types.*

Next up is the question number. The question number defines the order of questions alphanumerically as long as a number of questions are shown on the same page. The number is also used to refer to the question.

The text of the question is what the user will be asked. There can be one text for each language defined in the settings.py file.

The extra is an additional piece of information shown to the user. As of yet not all questions support this, but most do.

An important aspect of questions (and their parents, QuestionSets) is the checks field. The checks field does a lot of things (possibly too many), the most important of which is to define if a certain question or questionset should be shown to the current subject.

The most important checks on the question are the following:

* **required** A required question must be answered by the user
* **requiredif="number,answer"**  Means that the question is required if the question with *number* is equal to *answer*.
* **shownif** Same as requiredif, but defining if the question is shown at all.
* **maleonly** Only shown to male subjects
* **femaleonly** Only shown to female subjects
* **iftag="tag"** Question is only shown if the given tag is in the RunInfo

Checks allow for simple boolean expressions like this:
`iftag="foo or bar"` or `requiredif="1,yes and 2,no"`

### Choice

A choice is a possible value for a multiple choice question.

### QuestionSet

A bunch of questions together form a questionset. A questionset is ultimately single page of questions. Questions in the same questionset are shown on the same page.

QuestionSets also have checks, with the same options as Questions. There's only one difference, **required** and **requiredif** don't do anything.

A questionset which contains no visible questions (as defined by **shownif**) is skipped.

### Answer

Contains the answer to a question. The value of the answer is stored as JSON.

### Questionnaire

A questionnaire is a bunch of questionsets together.
