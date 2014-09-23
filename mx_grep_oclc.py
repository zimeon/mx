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
import datetime

class mx_grepper:
    def __init__(self, show_dupes=False):
        # Options
        self.show_dupes=show_dupes
        # Stats collected over run
        self.records_seen = 0
        self.records_matched = 0
        self.fields_matched = 0
        self.fields_bad = 0
        self.fields_duped = 0
        # Use for parsing each record
        self.bibid = 'unknown_bibid'

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
        be a decimal number. In some cases there are 'ocm', 'ocn', or 
        'OCM' prefixes (what do they mean?). Usually these are duplicate
        entries.

        Any leading or trailing whitespace is silently ignored.

        What does it mean to have genuinely different numbers? e.g.
        http://newcatalog.library.cornell.edu/catalog/302435
        which has both OCLC nums 3615963 and 9860311 

        What does it mean to have space separated data? I assume these
        are error cases. e.g.
        #4958095 'ocm35304571 96047844'
        """
        oclcnums = {}
        for f035 in record.get_fields('035'):
            ref = f035['a']
            if (ref is not None): 
                # strip leading or trailing whitespace
                ref = ref.lstrip().rstrip()
                m = re.match(r'\(OCoLC\)(.+)$',ref)
                # has (OCoLC) prefix...
                if (m):
                    self.fields_matched += 1
                    entry = m.group(1)
                    m2 = re.match(r'^(ocm|ocn|OCM)?(\d+)$',entry)
                    if (m2):
                        ref = m2.group(2)
                        if (ref in oclcnums):
                            # dupe
                            self.fields_duped += 1
                            if (self.show_dupes):
                                logging.warning("[%s] Dupe 035$a OCLC value: '%s'",self.bibid,ref) 
                        else:
                            oclcnums[ref] = 1
                    else:
                        self.fields_bad += 1
                        logging.warning("[%s] Bad 035$a OCLC entry: '%s'",self.bibid,entry)
        return sorted(oclcnums.keys())

# Options and arguments
__version__ = '0.0.1'
LOGFILE = 'mx_grep_oclc.log'
p = optparse.OptionParser(description='MARCXML Record Grepper -- currently just deals with the special case of looking for OCLC refs',
                          usage='usage: %prog [[opts]] [file1] .. [fileN]',
                          version='%prog '+__version__ )
p.add_option('--logfile', action='store', default=LOGFILE,
             help="Log file name (default %s)" % (LOGFILE))
p.add_option('--dupes', action='store_true',
             help="issue warnings for duplicate data")
p.add_option('--verbose', '-v', action='store_true',
             help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

logging.basicConfig(filename=opt.logfile)
logging.warning("STARTED at %s" % (datetime.datetime.now()))

# Loop over all files specified looking at each records
files = 0
mg = mx_grepper(show_dupes=opt.dupes)
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

logging.warning("FINISHED at %s" % (datetime.datetime.now()))
