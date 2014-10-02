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
    def __init__(self, dupeslog=None):
        # Options
        self.dupeslog=dupeslog
        # Stats collected over run
        self.records_seen = 0
        self.records_matched = 0
        self.records_multi = 0
        self.fields_matched = 0
        self.fields_bad = 0
        self.fields_esuffix = 0
        self.fields_duped = 0
        # Use for parsing each record
        self.bibid = 'unknown_bibid'

    def grep(self,record): 
        #print pymarc.record_to_xml(record)
        self.records_seen += 1
        # Everything should have local bibid as 001
        #
        # At Cornell this is just a number. In Harvard this data has a check
        # digit appended with hyphen so must treat as string.
        self.bibid = 'unknown_bibid'
        try:
            self.bibid=record['001'].value()
            oclcnums = self.get_oclcnums(record)
            if (len(oclcnums)>0):
                print "%s\t%s" % (self.bibid,' '.join([str(x) for x in oclcnums]))
                self.records_matched += 1
        except ValueError as e:
            logging.warning("Bad record '%s': %s" % (self.bibid,str(e)))

    def get_oclcnums(self,record):
        """Look for one or more OCLC identifiers for record

        OCLC numbers are recorded in 035$a (repeatable) or 079$a (not
        repeatable). The OCLC number itself should be a decimal number 
        and we need to cater for sometimes it being zero padded to some 
        length. Any leading or trailing whitespace is silently ignored.

        From Chiat Naun Chew about prefixes: "OCLC outputs OCLC numbers 
        in several alternative formats, one of which is with an ocm/ocn 
        prefix. There is no significance to the difference between the 
        prefixes - one just came into use later than the other. The 079 
        field is where the OCLC number of the corresponding master record 
        is stored in institution records. (As output by OCLC, the 035 of 
        institution records contains the record ID for the institution 
        record, not the master record)."

        Cornell data - Usually the OCLC numbers have a prefix '(OCoLC)'. 
        In some cases there are also 'ocm', 'ocn', or 'OCM' prefixes. 
        Usually these are duplicate entries. Some entries have leading
        and trailing spaces.

        Harvard data - Paul Deschner writes "A quick check shows that 
        11.3 million of our 13.6 million bib records have "ocn*" or 
        "ocm*" OCLC nums in 035 subfield a and less than 1,000 have 
        "*OCoLC*" nums.

        Stanford data - See code used for indexer at 
        https://github.com/sul-dlss/solrmarc-sw/blob/master/stanford-sw/src/edu/stanford/StanfordIndexer.java#L691
        Usual prefix is '(OCoLC-M)' else can be '(OCoLC)' in 035$a or
        else 'ocm' or 'ocn' is 079$a.

        What does it mean to have genuinely different numbers? e.g.
        http://newcatalog.library.cornell.edu/catalog/302435
        which has both OCLC nums 3615963 and 9860311 

        Sometimes we find that there are entries with separated data, report these
        as error cases. e.g.
        #at Cornell: bibid=4958095 'ocm35304571 96047844'
        """
        oclcnums = set()
        for field in ['035','079']:
            for f in record.get_fields(field):
                ref = f['a']
                if (ref is not None): 
                    # strip leading or trailing whitespace
                    ref = ref.lstrip().rstrip()
                    m = re.match(r'(\(ocolc\)|\(ocolc-m\)|ocm|ocn|on)(.+)$',ref,flags=re.IGNORECASE)
                    # has (OCoLC) prefix...
                    if (m):
                        self.fields_matched += 1
                        entry = m.group(2)
                        m2 = re.match(r'^(ocm|ocn|on)?(\d+)$',entry,flags=re.IGNORECASE)
                        if (m2):
                            oclcnum = int(m2.group(2))
                            if (oclcnum in oclcnums):
                                # dupe
                                self.fields_duped += 1
                                if (self.dupeslog):
                                    self.dupeslog.warning("[%s] Dupe in %s$a of OCLC value: '%d'",self.bibid,field,oclcnum) 
                            else:
                                oclcnums.add(oclcnum)
                        elif (re.match(r'(ocm|ocn|on)?(\d+)e$',entry,flags=re.IGNORECASE)):
                            self.fields_esuffix += 1
                            logging.warning("[%s] Ignored e-suffixed %s$a OCLC entry: '%s'",self.bibid,field,entry)
                        else:
                            self.fields_bad += 1
                            logging.warning("[%s] Ignored bad %s$a OCLC entry: '%s'",self.bibid,field,entry)
            if (len(oclcnums)>1):
                self.records_multi += 1
                logging.warning("[%s] Multi: Have %d OCLC nums: %s",self.bibid,len(oclcnums)," ".join([str(x) for x in oclcnums]))
        return sorted(oclcnums)

# Options and arguments
LOGFILE = 'mx_grep_oclc.log'
p = optparse.OptionParser(description='MARCXML Record Grepper -- currently just deals with the special case of looking for OCLC refs',
                          usage='usage: %prog [[opts]] [file1] .. [fileN]')
p.add_option('--logfile', action='store', default=LOGFILE,
             help="Log file name (default %s)" % (LOGFILE))
p.add_option('--dupeslog', action='store', default=None,
             help="Log file to write duplicate warnings")
p.add_option('--xml', action='store_true',
             help="Records are MARCXML")
p.add_option('--marc21', action='store_true',
             help="Records are MARC21")
p.add_option('--verbose', '-v', action='store_true',
             help="verbose, show additional informational messages")
(opt, args) = p.parse_args()
if (opt.xml and opt.marc21):
    logging.error("Cannot use both --xml and --marc21 options!")
    exit(2)

logging.basicConfig(filename=opt.logfile)
logging.warning("STARTED at %s" % (datetime.datetime.now()))

dupeslog = None
if (opt.dupeslog):
    dupeslog = logging.getLogger(name='dupeslog')
    f = logging.FileHandler(filename=opt.dupeslog,mode='w')
    dupeslog.addHandler(f)
    dupeslog.warning("#DUPES LOG STARTED at %s" % (datetime.datetime.now()))

# Loop over all files specified looking at each records
files = 0
mg = mx_grepper(dupeslog=dupeslog)
print "#bibid oclcnum[s]"
for arg in args:
    fh = None
    files += 1
    # Is this MARCXML or MARC21? If option not specified then 
    # guess from file name
    is_xml = ( True if opt.xml else ( False if opt.marc21 else None ) )
    if (is_xml is None):
        if (re.search(r'xml(\.gz)?$',arg)):
            is_xml = True
        elif (re.search(r'(marc21|marc|mrc)(\.gz)?$',arg)):
            is_xml = False
        else:
            logging.warning("Cannot tell file type, defaulting to MARCXML");
            is_xml = true
    if (is_xml):
        if (re.search(r'\.gz$',arg)):
            logging.warning("#Reading %s as gzipped MARCXML" % (arg))
            if (opt.verbose):
                print "#Reading %s as gzipped MARCXML" % (arg)
            fh = gzip.open(arg,'rb')
        else:
            logging.warning("#Reading %s as MARCXML" % (arg))
            if (opt.verbose):
                print "#Reading %s as MARCXML" % (arg)
            fh = open(arg,'rb')
        reader = pymarc.MARCReader(fh)
        pymarc.map_xml(mg.grep, fh)
    else:
        if (re.search(r'\.gz$',arg)):
            logging.warning("#Reading %s as gzipped MARC21" % (arg))
            if (opt.verbose):
                print "#Reading %s as gzipped MARC21" % (arg)
            fh = gzip.open(arg,'rb')
        else:
            logging.warning("#Reading %s as MARC21" % (arg))
            if (opt.verbose):
                print "#Reading %s as MARC21" % (arg)
            fh = open(arg,'rb')
        reader = pymarc.MARCReader(fh,to_unicode=True)
        pymarc.map_records(mg.grep, fh)
if (len(args)>1):
    print "# %d files" % files
print "# %d records seen, %d matched, %d multi-valued" % (mg.records_seen,mg.records_matched,mg.records_multi)
print "# %d field matches, %d duplicate entries, %d bad entries, %d e-suffixed (ignored)" % (mg.fields_matched,mg.fields_duped,mg.fields_bad,mg.fields_esuffix)

logging.warning("FINISHED at %s" % (datetime.datetime.now()))
