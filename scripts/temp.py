#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# @file   temp.py
# @author Albert Puig (albert.puig@cern.ch)
# @date   02.11.2014
# =============================================================================
"""Measure the Raspberry Pi temperature."""

from __future__ import with_statement
import os
import cPickle
import subprocess


DATAFILE = 'temps.dat'

def get_temp():
    output = [line for line in subprocess.Popen(['/opt/vc/bin/vcgencmd', 'measure_temp'],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT).communicate()[0].split('\n') if line]
    if len(output) != 1:
        return 0.0
    output = output[0]
    return float((output.split('=')[1]).split("'")[0])


def get_data():
    if not os.path.exists(DATAFILE):
        return None, None, None, None
    with open(DATAFILE) as f:
        temp_sum, temp_max, temp_min, n_measures = cPickle.load(f)
    return temp_sum, temp_max, temp_min, n_measures


def save_data(temp_sum, temp_max, temp_min, n_measures):
    with open(DATAFILE, 'w') as f:
        cPickle.dump((temp_sum, temp_max, temp_min, n_measures), f)

if __name__ == '__main__':
    temp_sum, temp_max, temp_min, n_measures= get_data()
    if not temp_sum:
        temp_sum = 0.0
        temp_max = 0.0
        temp_min = 100.0
        n_measures = 0
    temperature = get_temp()
    if temperature:
        temp_sum += temperature
        temp_max = max(temp_max, temperature)
        temp_min = min(temp_min, temperature)
        n_measures += 1
    save_data(temp_sum, temp_max, temp_min, n_measures)

# EOF
