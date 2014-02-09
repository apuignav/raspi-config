from __future__ import with_statement
import os

import cPickle

def load(filename):
  if not os.path.exists(filename):
    return None
  with open(filename) as f:
    decoded = cPickle.load(f)
  return decoded

def write(filename, obj):  
  with open(filename, 'w') as f:
    cPickle.dump(obj, f)

