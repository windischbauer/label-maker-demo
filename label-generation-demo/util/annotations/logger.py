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

import logging.config
from functools import wraps

from util import string_convenience as rs

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('Default')


def log(func, verbose=False):
    @wraps(func)
    def with_logging(*args, **kwargs):
        args_print_string = rs.reduce_middle(
            s=f'{args}', length=16) if not verbose else f'{args}'
        kwargs_print_string = rs.reduce_middle(
            s=f'{kwargs}', length=16) if not verbose else f'{kwargs}'
        logger.info(
            f'{func.__name__}{args_print_string} {kwargs_print_string} called')
        value = func(*args, **kwargs)
        value_print_string = rs.reduce_middle(
            s=f'{value}', length=16) if not verbose else f'{value}'
        logger.info(
            f'{func.__name__}{args_print_string} {kwargs_print_string} returned {value_print_string}')
        return value

    return with_logging
