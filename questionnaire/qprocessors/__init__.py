from django.conf import settings
from questionnaire import *
from django.utils.translation import ugettext as _

import simple       # store value as returned
import choice       # multiple choice, do checks
import range        # range of numbers
import timeperiod   # time periods
import custom       # backwards compatibility support
