#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# @file   retry.py
# @author Albert Puig (albert.puig@cern.ch)
# @date   31.05.2016
# =============================================================================
"""Retry decorator from the python wiki."""

import time
from functools import wraps

import logging

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    Arguments:
        ExceptionToCheck (Exception, tuple): the exception to check. may be a tuple of
            exceptions to check

        tries (int): number of times to try (not retry) before giving up
        delay (int): initial delay between retries in seconds
        backoff (int) backoff multiplier e.g. value of 2 will double the delay
            each retry

    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, error:
                    msg = "%s, Retrying in %d seconds..." % (str(error), mdelay)
                    logging.debug(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry

# EOF
