#!/usr/bin/env python
#
# Simple MARCXML "grepper"
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
import logging

class mx_grepper:
    def __init__(self):
        self.records_seen = 0
        self.records_matched = 0
        self.fields_matched = 0

    def grep(self,record): 
        self.records_seen += 1
        # Everything should have local bibid as 001
        bibid = 'unknown_bibid'
        try:
            bibid=record['001'].value()
            # Now look for OCLC nums
            f035=record['035']
            if (f035):
                oclcnums = []
                for ref in f035.get_subfields('a'):
                    #print "%s %s" % (bibid,ref)
                    m = re.match(r'\(OCoLC\)(\d+)$',ref)
                    if (m):
                        oclcnums.append(m.group(1))
                        self.fields_matched += 1
                if (len(oclcnums)>0):
                    print "%s\t%s" % (bibid,' '.join(oclcnums))
                    self.records_matched += 1
        except Exception as e:
            logging.warning("Bad record '%s': %s" % (bibid,str(e)))

# Options and arguments
__version__ = '0.0.1'
p = optparse.OptionParser(description='MARCXML Record Grepper -- currently just deals with the special case of looking for OCLC refs',
                          usage='usage: %prog [[opts]] [file1] .. [fileN]',
                          version='%prog '+__version__ )
p.add_option('--verbose', '-v', action='store_true',
              help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

# Loop over all files specified looking at each records
files = 0
mg = mx_grepper()
print "#bibid oclcnum[s]"
for arg in args:
    fh = 0
    if (re.search(r'\.gz$',arg)):
        if (opt.verbose):
            print "#Reading %s as gzipped MARCXML" % (arg)
        fh = gzip.open(arg,'rb')
    else:
        if (opt.verbose):
            print "#Reading %s as MARCXML" % (arg)
        fh = open(arg,'rb')
    files += 1
    reader = pymarc.MARCReader(fh)
    pymarc.map_xml(mg.grep, fh)
if (len(args)>1):
    print "# %d files" % files
print "# %d records seen, %d matched, %d field matches" % (mg.records_seen,mg.records_matched,mg.fields_matched)
