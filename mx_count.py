#!/usr/bin/env python
#
# Simple MARCXML Record Counter
#
# Based on example code for pymarc at
# https://github.com/edsu/pymarc/blob/master/test/xml_test.py
# (every place pymarc takes a file name a handle works fine as
# the underlying xml.sax works that way, hence can open a gzip
# and pass in handle directly)
import sys
import gzip
import pymarc
import re
import optparse

seen = 0

def count(record): 
    global seen
    seen += 1

# Options and arguments
__version__ = '0.0.1'
p = optparse.OptionParser(description='MARCXML Record Counter',
                          usage='usage: %prog [[opts]] [file1] .. [fileN]',
                          version='%prog '+__version__ )
p.add_option('--verbose', '-v', action='store_true',
              help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

# Loop over all files specified counting records in each
total = 0
fmt = "%-7d %s"
for arg in args:
    seen = 0
    fh = 0
    if (re.search(r'\.gz$',arg)):
        if (opt.verbose):
            print "Reading %s as gzipped MARCXML" % (arg)
        fh = gzip.open(arg,'rb')
    else:
        if (opt.verbose):
            print "Reading %s as MARCXML" % (arg)
        fh = open(arg,'rb')
    pymarc.map_xml(count, fh)
    print fmt % (seen,arg)
    total += seen
if (len(args)>1):
    print fmt % (total,'TOTAL')
