# Description: This file contains custom filters for use in Django templates. The functions are compatible with testing in the Python shell via F5.

from django import template
from django.template import Library
from django.template.defaultfilters import date
from django.contrib.humanize.templatetags.humanize import naturaltime, naturalday
from datetime import timedelta, datetime
# These are for overriding linebreaks_filter.
from django.utils.safestring import mark_safe, SafeData
from django.utils.html import escape
from django.utils.text import normalize_newlines
import re

register = Library()

@register.filter(name='format')
# This filter allows Python's format function to be used in the template. Django has a stringformat filter, based on the pre-Python 3.1 printf function that does the same thing, but without
# commas, a floatformat filter that only rounds and converts to a string, and a separate intcomma filter, which works with both integers and floats. This function replaces all of those with
# a filter that uses the same syntax for its argument as the format function, which students of Computer Science I with Python 3 have been instructed to memorize.
#
# This function also improves on the format function by being able to handle values that have been returned as a string, even though the value would be a valid integer or float when converted. Some
# Django features return numbers as strings. For example, the django-hitcount add-on stores the hits using the format "1000", and I wanted to format it as "1,000".
def format_in_template(value, formatting_instructions):
    try:
        return format(value, formatting_instructions)
    except ValueError:
        if 'd' in formatting_instructions:
            return format(int(value), formatting_instructions)
        elif 'f' in formatting_instructions:
                return format(float(value), formatting_instructions)
        else:
            raise ValueError("A value other than a float or integer was passed to the format filter, and it could not be processed.")

@register.filter(name='times')
# By default, you can only use a for loop in the template when iterating over the entire length of a data structure.
# This functions allow iterating an arbitrary number in the template.
def times(number):
    return range(number)

@register.filter(name='range')
# This function allows iterating over a range in the template.
def filter_range(start, end):
    return range(start, end)

@register.filter(name='index')
# This function allows using indices in the template. The length can't be passed as an argument, so use "last" filter to reference the last element. 
def index(value, i):
    return value[int(i)]

@register.filter(name='last')
# This function overrides Django's built-in last filter to extends support to querysets.
# The built-in filter works by using the -1 index, which won't work for querysets.
def last(value):
    last = None

    try:
        last = value[-1]
    except AssertionError:
        # If "AssertionError: Negative indexing is not supported" occurs because the value is a queryset, use an alternate syntax.
        try:
            # Use this syntax because the traditional syntax, "len(last)-1", will evaluate to -1 when the queryset is empty.
            last = value.reverse()[0]
        except IndexError:
            # When the list or queryset is empty, return None.
            pass

    return last

@register.filter(name='attribute')
# This function is used with a list of dictionaries or objects. Use it after the "index" filter to return the value for a key or attribute.
def attribute(structure, value):
    if str(type(structure)) == "<class 'dict'>":
        # The data structure is a dictionary.
        return eval("structure['"+value+"']")
    else:
        # The data structure is an object.
        return eval("structure."+value)

# I added functions for arithmetic operations in order to be able to calculate the total iteration of a nested for loop, so that it wouldn't go beyond the length of a list.
# The add filter is the only one that is built-in.
@register.filter(name='mul')
def mul(value, factor):
    return value * factor

@register.filter(name='sub')
def sub(value, subtrahend):
    return value - subtrahend

@register.filter(name='mod')
def mod(value, modulus):
    return value % modulus

# A0. Format an amount of elapsed time.
# Input: value, an int or float. By default, this is in seconds.
# unit, an optional string for when the units passed to value are milliseconds, not seconds. It can be the full name ("milliseconds") or an abbreviation ("ms").
# Only milliseconds and seconds are supported, because these are the only common output units. Milliseconds will be converted to seconds in the output.
#
# Output: The formatting and conversion ratios are the same as the built-in timesince and timeuntil filters: a human-readable string such as '5
# seconds' or '1 month, 17 days'. The only behavioral difference is that seconds will be shown instead of rounded to 0 minutes, and if the value is
# less than a second, there will be up to three decimal places. Only the two largest adjacent units are shown. Weeks, however, will be shown only when
# they are the largest unit. This function uses 365-day years and 30-day months.
#
# Template syntax examples: {{ stopwatch_result | timeelapsed }}, {{ stopwatch_result | timeelapsed:"ms" }}
@register.filter(name='timeelapsed')
def timeelapsed(value, unit=None):
    if value == 0:
        return '0 seconds'
    # Convert to seconds. If the value is more than 1 second, then round down to integer seconds.
    if (unit == "milliseconds" or unit == "ms") and value >= 1000:
        value //= 1000
    else:
        if (unit == "milliseconds" or unit == "ms") and value < 1000:
            value /= 1000
            return format(value, '.3f') + ' seconds'
    # If the time elapsed is under 60 seconds, sidestep the rest of the procedure; go ahead and return the result now. 
    if value < 60:
        return handle_plurals(value, 'seconds')
    seconds = value % 60
    value //= 60
    minutes = value % 60
    value //= 60
    hours = value % 24
    value //= 24
    # If weeks are the largest unit, then use mod 7. If months or years are the largest unit, then use mod 30.
    if value < 30:
        days = value % 7
        value //= 7
        weeks = value % 7
        months = 0
        years = 0
    else:
        days = value % 30
        value //= 30
        weeks = 0
        months = value % 12
        years = value // 12
    years_string = handle_plurals(years, 'years')
    months_string = handle_plurals(months, 'months')
    weeks_string = handle_plurals(weeks, 'weeks')
    days_string = handle_plurals(days, 'days')
    hours_string = handle_plurals(hours, 'hours')
    minutes_string = handle_plurals(minutes, 'minutes')
    seconds_string = handle_plurals(seconds, 'seconds')
    if years_string != '':
        if months_string != '':
            return years_string + ', ' + months_string
        else:
            return years_string
    elif months_string != '':
        if days_string != '':
            return months_string + ', ' + days_string
        else:
            return months_string
    elif weeks_string != '':
        if days_string != '':
            return weeks_string + ', ' + days_string
        else:
            return weeks_string
    elif days_string != '':
        if hours_string != '':
            return days_string + ', ' + hours_string
        else:
            return days_string
    elif hours_string != '':
        if minutes_string != '':
            return hours_string + ', ' + minutes_string
        else:
            return hours_string
    elif minutes_string != '':
        if seconds_string != '':
            return minutes_string + ', ' + seconds_string
        else:
            return minutes_string
    else:
        return seconds_string

# A1. This function is only useful for returning a value to 'timeelapsed'. Return the number and unit, using the plural of the unit if the amount is greater than 1.
# Return an empty string if the amount is 0. This function takes advantage of all units in the parent 'timeelapsed' function using 's'.
# Input example: 1, 'seconds'. Abbreviations are not accepted.
# Output example: '1 second'
def handle_plurals(amount, unit):
    if amount == 1:
        return '1 '+unit[0:len(unit)-1]
    elif amount == 0:
        return ''
    else:
        return str(amount) + ' ' + unit

@register.filter(name='naturalday')
# This function exists to register the naturalday filter without having to register the rest of the contrib-humanize module,
# which I probably won't use.
def register_naturalday(value, date_args):
    return naturalday(value, date_args)

@register.filter(name='naturaltime_with_dates')
# Naturaltime returns the elapsed time since or until a date by calling the timesince or timeuntil filter. Unlike those filters, it doesn't accept an argument
# other than "now" because it ends with "ago" or "from now", and it returns with second precision instead of minute precision. It also replaces "1" with "a" or "an" for
# an elapsed time that is one second, one minute, or one hour. This function extends naturaltime by allowing more arguments, all optional, for more customization.

# The first three paramaters are for returning a date instead of an elapsed time. This is for a situation where, instead of literally wanting an amount of time,
# the user wants to know when something happened, and past a certain amount of time like "4 days ago", the date itself becomes more human-readable.
# 1. "time_threshhold" is the amount of time past which the switch to date rendering occurs. The lowest possible unit is "day".
#    Other formats include "2 days" to "6 days", "week", "3 weeks", "month", "2 months", "year", "3 years". Defaults to "month".
# 2. "date_args" is a formatting string which uses the same syntax as the date tag's formatted string -- see its documentation on the Django website. If you don't pass an argument,
# then the filter will only used elapsed times, never dates.
# 3. "prefix" is an optional string like "on " or "at " for using the formatted datetime in a sentence.

# 4. "token_for_one" determines whether you want to use "1", "one", or "a" or "an" for seconds, minutes, and hours. It defaults to using "1", because
# I think this looks better when the variable is by itself in the layout (e.g. top-right corner). If you were want to use this variable in a sentence,
# you would also probably need to set "prefix". Set token_for_one='one' or token_for_one='a or an' to override the default.
#
# In order to work around Django's two argument limitation, this filter uses a different syntax with a dictionary wrapped in string delimiters.
# {{ value | "{'parameter':'argument'}" }}
def naturaltime_with_dates(value, d = "{}" ):
    if value == '':
        # The value is an empty string, which really only happens when something very unusual has happened, like an upload being deleted by a
        # moderator and the page failing to redirect immediately afterward. An empty value needs to be returned because the rest of the program
        # expects a datetime object, and passing a string can cause exceptions. For example, a datetime object's replace method accepts keyword
        # arguments, and a string's replace method doesn't, so passing a string will raise "TypeError: replace() takes no keyword arguments".
        return value
    else:
        # Work around Django's two argument limitation. Unpack the dictionary.
        d=eval(d)
        if 'time_threshhold' in d:
            time_threshhold = d['time_threshhold']
        else:
            time_threshhold = 'month'
        if 'date_args' in d:
            date_args = d['date_args']
        else:
            date_args = ''
        if 'prefix' in d:
            prefix = d['prefix']
        else:
            prefix = ''
        if 'token_for_one' in d:
            token_for_one = d['token_for_one']
        else:
            token_for_one = "1"
        
        natural_time = naturaltime(value)
        if token_for_one != 'a or an' and token_for_one != 'a' and token_for_one != 'an':
            natural_time = natural_time.replace('a ', token_for_one + ' ').replace('an ', token_for_one + ' ')
        if date_args != '' and is_over_time_threshhold(value, time_threshhold):
            return prefix + date(value, date_args)
        else:
            return natural_time

# Determine whether naturaltime_with_dates(), based on its settings, should format a datetime as "X units ago" or return the date.
# Input: value, the datetime to be formatted. time_threshhold, a string like "4 days" or "week".
# Output: True or False
def is_over_time_threshhold(value, time_threshhold):
    if " " in time_threshhold:
        number_and_unit = time_threshhold.split()
        number = int(number_and_unit[0])
        unit = number_and_unit[1]
    else:
        unit = time_threshhold
        if "s" in time_threshhold:
            number=2
        else:
            number=1
        
    if "year" in unit:
        if abs(value.replace(tzinfo=None) - datetime.now()) >= timedelta(weeks=number*52):
            return True
        else:
            return False
    elif "month" in unit:
        if abs(value.replace(tzinfo=None) - datetime.now()) >= timedelta(weeks=number*4):
            return True
        else:
            return False
    elif "week" in unit:
        if abs(value.replace(tzinfo=None) - datetime.now()) >= timedelta(weeks=number):
            return True
        else:
            return False
    else:
        if "day" in unit:
            if abs(value.replace(tzinfo=None) - datetime.now()) >= timedelta(days=number):
                return True
            else:
                return False

@register.filter(name='largest_time_unit')
# Modifies one of the other Django filters for elapsed time, including previous custom filters.
# Use only the largest unit of time, in order to keep within a certain amount of space in the layout. The output will be, at most, 14 characters.
def largest_time_unit(string):
    # If there is a comma, the position of the first comma will be used to remove everything between the comma and "ago" or "from now", plus the comma.
    first_comma_position = string.find(",")
    if first_comma_position == -1:
        # The elapsed time has only one unit, so the function doesn't need to do anything else.
        return string
    else:
        second_delimiter = string.find(" ago")
        if second_delimiter == -1:
            second_delimiter = string.find(" from now")
            if second_delimiter == -1:
                # The string is a date from naturaltime_with_dates that occurred more than a week ago.
                return string
        # Return the modified string.
        return string[0:first_comma_position] + string[second_delimiter:]

@register.filter(name='one_letter_time_unit')
# Modifies one of the other Django filters for elapsed time, including previous custom filters. Use only the first letter or two of the largest unit
# of time in order to save space for mobile. You can use both the full string and the abbreviated string with CSS that will show the appropriate one depending on the viewport width.
# Because many languages have time units begin with the same letter, rendering with function will also make internationalization easier.
# If keep_suffix=True, then the filter doesn't remove the " ago" or " from now" part of the string. The output will be, at most, four characters.
def one_letter_time_unit(string, keep_suffix = False):
    string = largest_time_unit(string)
    # Obtain the number associated with the largest unit. The naturaltime function's source code specifies that, for reasons unbeknownst to me, it places a nonbreaking space in Unicode
    # between the count number and the unit. If the string doesn't contain a nonbreaking space, then either the string begins with "a" or "an", or the largest unit is days or greater,
    # which use a regular space after the count number instead.
    space_position = string.find('\u00A0')
    if space_position == -1:
        space_position = string.find(' ')
    number_string = string[0:space_position]
    # Account for filters that use "a" or "an" instead of 1.
    if number_string == "a" or number_string == "an":
        number_string = "1"
    
    suffix = ''
    if keep_suffix:
        if ' ago' in string:
            suffix = ' ago'
        else:
            if ' from now' in string:
                suffix = ' from now'

    if 'year' in string:
        abbrev = 'y'
    elif 'month' in string:
        abbrev = 'mo'
    elif 'week' in string:
        abbrev = 'w'
    elif 'day' in string:
        abbrev = 'd'
    elif 'hour' in string:
        abbrev = 'h'
    elif 'minute' in string:
        abbrev = 'm'
    elif 'second' in string:
        abbrev = 's'
    else:
        # The string is a date from naturaltime_with_dates that occurred more than a week ago.
        return string
    return number_string + abbrev + suffix

@register.filter(name='humanize_list')
# Display a Python list of nouns as they would appear in a sentence. Display ['A', 'B'] as 'A and B'. Display ['A', 'B', 'C'] as 'A, B, and C'.
# The conjunction can be overriden with "or". It can turned off by passing an empty string, as in {{ value | text_list:"" }}, for the format 'A, B'.
# Django saves values from multiselects in a form as a list converted to a string, as in "['A', 'B', 'C']". This filter is also able to handle this data type directly.
# Input: First, a list or a list wrapped in string delimiters. A tuple will also work. Second, an optional string. This can be "and", "or", or "". It defaults to "and".
# Output: A string containing all the elements in the list. If the list has no elements, the filter returns an empty string.
def humanize_list(value, conjunction="and"):
    if str(type(value)) == "<class 'str'>":
        value = eval(value)
    if conjunction == "":
        return ', '.join(value)
    else:
        if len(value) == 0:
            return ''
        if len(value) == 1:
            return value[0]
        elif len(value) == 2:
            return value[0] + ' ' + conjunction + ' ' + value[1]
        else:
            return ', '.join(value[0:len(value)-1]) + ', ' + conjunction + ' ' + value[len(value)-1]

@register.filter(name='format_currency')
# Format a float as a string containing a dollar amount. Return an empty string if the value is None.
# If exact=True, it will follow the examples $1,349.99 and $1,350.00.
# If exact=False, it will follow the examples $1,349.99 and $1,350. The former is more appropriate for a shopping site. The latter is more appropriate for
# using the value in a sentence, such as on a shelter/rescue website.
def format_currency(value, exact=True):
    if value == None:
        return ''
    else:
        dollars = "$" + format(value, ",.2f")
        if exact:
            return dollars
        else:
            if dollars.endswith(".00"):
                return dollars[0:len(dollars)-3]

# Modify the linebreaks filter to merge paragraphs that are under a certain minimum character count. The default is 0, meaning this modification maintains backwards-compatibility.
@register.filter("linebreaks", is_safe=True, needs_autoescape=True)
def linebreaks_filter(value, min_paragraph_length=0, autoescape=True):
    """
    Replaces line breaks in plain text with appropriate HTML; a single
    newline becomes an HTML line break (``<br />``) and a new line
    followed by a blank line becomes a paragraph break (``</p>``).
    """
    autoescape = autoescape and not isinstance(value, SafeData)
    return mark_safe(linebreaks(value, min_paragraph_length, autoescape))

def linebreaks(value, min_paragraph_length=0, autoescape=False):
    """Converts newlines into <p> and <br />s."""
    value = normalize_newlines(value)
    paras = re.split('\n{2,}', value)
    for i in range(len(paras)-1):
        if len(paras[i]) < min_paragraph_length:
            paras[i] = paras[i] + " " + paras[i+1]
            paras.pop(i+1)
    if autoescape:
        paras = ['<p>%s</p>' % escape(p).replace('\n', '<br />') for p in paras]
    else:
        paras = ['<p>%s</p>' % p.replace('\n', '<br />') for p in paras]
    return '\n\n'.join(paras)

