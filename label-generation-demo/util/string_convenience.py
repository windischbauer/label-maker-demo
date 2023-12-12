#  Copyright (c) 2023. Dynatrace LCC. All Rights Reserved.

#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied. See the License for the specific language governing
#  permissions and limitations under the License.


import datetime
import re


def reduce_string(s, length):
    return (s[:length] + ' ..') if len(s) > length + 3 else s


def reduce_middle(s, length):
    return (s[:int(length / 2)] + ' ... ' + s[int(-length / 2):]) if len(s) > length + 5 else s


# Remove underscores and capitalize first letter of each word
def display_labels(label):
    return re.sub(r'_', ' ', label).title()


def make_code_label(label):
    return re.sub(r' ', '_', label.upper())


def translate_rule_name(rule):
    return "rule_" + re.sub(r'(-| )', '_', rule)


def wrap_lookup(feature):
    res = ''
    feat = feature.split(' ')
    for f in feat:
        if re.match(r'^[if|else|return|True|False|not|and|or]', f):
            continue
        if re.match(r'^[a-zA-z]', f):
            res += 'lookup(x, "' + f + '")'
        elif re.match(r'\(+[a-zA-z]', f):
            res += '(' + wrap_lookup(f[1:])
        else:
            res += f
        res += ' '
    return res


def replace_binop(rule):
    res = re.sub(r'\|', 'or', rule)
    res = re.sub(r'&', 'and', res)
    return res


def display_dict(d):
    res = ''
    for key in d:
        res += display_labels(key) + ': ' + str(d[key]) + '   \n'
    return res


# escape line breaks in a string by using a backslash


def escape_line_breaks_in_rules(s):
    s['rule'] = re.sub(r'\n', r'\\n', s['rule'])
    return s


# Define a function that returns a string representation of a datetime object. When the date is today, don't show the date, just the time.
# Otherwise, show the date and time.


def display_date(date, no_year=False):
    if date.date() == datetime.date.today():
        return str(date.strftime("%H:%M:%S"))
    else:
        if no_year:
            return str(date.strftime("%m-%d %H:%M:%S"))
        return str(date.strftime("%Y-%m-%d %H:%M:%S"))
