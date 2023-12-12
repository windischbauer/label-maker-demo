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
import time
from functools import wraps

from util import string_convenience as rs

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('Benchmark')


def benchmark(func, verbose=False):
    @wraps(func)
    def function_timer(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)
        end = time.time()
        runtime = end - start
        args_print_string = rs.reduce_middle(
            f'{args}', 16) if not verbose else f'{args}'
        kwargs_print_string = rs.reduce_middle(
            f'{kwargs}', 16) if not verbose else f'{kwargs}'
        logger.debug(
            f'{func.__name__}{args_print_string} {kwargs_print_string} took {runtime:.4f} seconds')
        return value

    return function_timer
