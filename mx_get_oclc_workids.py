#!/usr/bin/env python
#
# Look for OCLC Work ids for our bibids base on oclcnum data
#
import sys
import gzip
import pymarc
import re
import optparse
import logging


class bibid_oclcnums(object):

    def __init__(self,file=None):
        self.bibids={}
        self.works={}
        if (file):
            self.read(file)

    def read(self,file):
        """Read in bibid to oclcnums data

        Ignores lines starting # and blank lines
        Take first entry in the case that there are dupes
        """
        fh = gzip.open(file,'r')
        n = 0
        for line in fh:
            n += 1
            if (re.match(r'\s*#',line) or not re.search(r'\S',line)):
                # ignore comment or blank
                pass
            else:
                d = line.split()
                if (len(d)<2):
                    logging.info("[%d] fewer than 2 elements, ignoring" % (n))
                else:
                    if (len(d)>2):
                        logging.info("[%d] ignoring extra %d elements for bibid %s" % (n,(len(d)-2),d[0]))
                    bibid = d[0]
                    oclcnum = d[1]
                    self.bibids[oclcnum]=bibid
        fh.close()
        logging.warning("read %d lines from %s, got %d entries" % (n,file,len(self.bibids)))

    def add_work(self,bibid,workid):
        """Add record of bibid being example of workid"""
        if (workid in self.works):
            # Add to list, already have one entry
            self.works[workid].append(bibid)
        else:
            # First bibid for this work
            self.works[workid]=[bibid]

    def write_works_data(self,file):
        """Write out OCLC workid to bibid mappings
        
        Write comment line to start. Other lines are workid followed by
        one or more bibids.
        """
        fh = gzip.open(file,'w')
        fh.write("#workid bibids\n")
        n = 0
        for workid in sorted(self.works):
            n += 1
            fh.write("%s %s\n" % (workid," ".join(self.works[workid])))
        fh.close()
        logging.warning("written %d lines to %s" % (n,file))

# Options and arguments
__version__ = '0.0.1'
p = optparse.OptionParser(description='Find OCLC workids for bibids given bibid-oclcnum and oclcnum-workid data',
                          usage='usage: %prog [bibid_oclcnums.gz] [oclc_concordance.gz] [works_out.gz',
                          version='%prog '+__version__ )
p.add_option('--dupes', action='store_true',
              help="issue warnings for duplicate data")
p.add_option('--verbose', '-v', action='store_true',
              help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

if (len(args)!=3):
    p.print_help()
    exit(1)

if (opt.verbose):
    logging.basicConfig(level=logging.INFO)

# Read bibid--oclcnum data into memory
bo = bibid_oclcnums(args[0])
print "Have %d bibid to oclcnum mappings" % (len(bo.bibids.keys()))

# Now open concordance and work through it looking for matches
#
# Concordance file from OCLC is 3.1GB with 343M lines. The 
# lines are formatted as:
#
# Column 1: every OCLC number found in a record from both 001 and 019
# Column 2: the current OCLC number for the record, from 001
# Column 3: the current Work ID associated with the record
#
# Look for matches in 1st or 2nd columns, get word identifier from
# 3rd column.
fh = gzip.open(args[1],'r')
n = 0
num1_matches = 0
num2_matches = 0
for line in fh:
    n += 1
    if (n%1000000 == 0):
        logging.warning("read %d lines from %s...." % (n,args[1]))
    (oclcnum1,oclcnum2,workid) = line.split()
    if (oclcnum1 in bo.bibids):
        bo.add_work(bo.bibids[oclcnum1],workid)
        num1_matches += 1
    elif (oclcnum2 in bo.bibids):
        bo.add_work(bo.bibids[oclcnum2],workid)
        num2_matches += 1
fh.close()
logging.warning("read %d lines from %s. %d matches in col1, %d in col2" % (n,args[1],num1_matches,num2_matches))

# Write out works data...
bo.write_works_data(args[2])
