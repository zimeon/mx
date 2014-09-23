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
        self.fields_bad = 0
        self.fields_duped = 0
        # Use for parsing each record

    def grep(self,record): 
        self.records_seen += 1
        # Everything should have local bibid as 001
        self.bibid = 'unknown_bibid'
        try:
            self.bibid=record['001'].value()
            oclcnums = self.get_oclcnums(record)
            if (len(oclcnums)>0):
                print "%s\t%s" % (self.bibid,' '.join(oclcnums))
                self.records_matched += 1
        except Exception as e:
            logging.warning("Bad record '%s': %s" % (self.bibid,str(e)))

    def get_oclcnums(self,record):
        """Look for one or more OCLC identifiers for record

        OCLC numbers are recorded in 035$a. The number itself should
        be a decimal number. In some cases there are 'ocm' or 'OCM'
        prefixes (what do they mean?). Usually these are duplicate
        entries.

        What does it mean to have genuinely different numbers? e.g.
        #4958095 ocm35304571 96047844
        """
        oclcnums = {}
        for f035 in record.get_fields('035'):
            ref = f035['a']
            if (ref is not None): 
                #print "#%s %s" % (self.bibid,ref)
                m = re.match(r'\(OCoLC\)(.+)$',ref)
                # has (OCoLC) prefix...
                if (m):
                    self.fields_matched += 1
                    entry = m.group(1)
                    m2 = re.match(r'^(ocm|OCM)?(\d+)$',entry)
                    if (m2):
                        ref = m2.group(2)
                        if (ref in oclcnums):
                            # dupe
                            self.fields_duped += 1
                        else:
                            oclcnums[ref] = 1
                    else:
                        self.fields_bad += 1
                        logging.warning("Bad 035$a OCLC entry in '%s': '%s'",self.bibid,entry)
        return sorted(oclcnums.keys())

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
print "# %d duplicate entries, %d bad entries" % (mg.fields_duped,mg.fields_bad)
