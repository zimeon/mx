#!/usr/bin/env python
#
# Look for OCLC Work ids that correspond with bibids based on 
# oclcnum data previously extracted and OCLC's concordance
# file of oclcnums to oclc work ids.
#
import sys
import gzip
import re
import optparse
import logging
import datetime

class bibid_oclcnums(object):

    def __init__(self,file=None,
                 dupeslog=None,
                 first_oclcnum_only=False,
                 write_workid_bibids=False,
                 write_oclcnum_workid_pairs=False,
                 write_pairs=None):
        # Options
        self.dupeslog=dupeslog
        self.first_oclcnum_only=first_oclcnum_only
        #
        self.bibids={}
        # Actions
        self.write_workid_bibids=write_workid_bibids
        if (self.write_workid_bibids):
            self.works={}
        self.write_oclcnum_workid_pairs=write_oclcnum_workid_pairs
        if (self.write_oclcnum_workid_pairs):
            # use set() to dedupe pairs, entries are csv strings
            self.oclccn2oclcwn=set()
        self.write_pairs=write_pairs
        if (self.write_pairs):
            # Set up output file
            self.ofh = gzip.open(self.write_pairs,'w')
            self.ofh.write("#workid bibid\n")
            self.ofh.write("#prefix workid with http://worldcat.org/entity/work/id/ to get URI\n")
            self.ofh.write("#prefix bibids with http://newcatalog.library.cornell.edu/catalog/ to get URI\n")
            self.ofh.write("#we expect many duplicate lines due to look up based on 001 and 019 OCLC data\n")
        # Read data if specified
        if (file):
            self.read_bibid_to_oclcnums(file)
            
    def read_bibid_to_oclcnums(self,file):
        """Read in bibid to oclcnums data

        Ignores lines starting # and blank lines
        Take first entry in the case that there are dupes
        """
        fh = gzip.open(file,'r')
        n = 0
        for line in fh:
            line = line.rstrip()
            n += 1
            if (re.match(r'\s*#',line) or not re.search(r'\S',line)):
                # ignore comment or blank
                pass
            else:
                d = line.split()
                if (len(d)<2):
                    logging.info("[%d] fewer than 2 elements, ignoring" % (n))
                else:
                    bibid = d[0] #not always integer
                    if (len(d)>2 and self.first_oclcnum_only):
                        logging.info("[%d] ignoring extra %d elements for bibid %s, line is '%s'" % (n,(len(d)-2),d[0],line))
                        self.add_oclcnum_to_bibid(int(d[1]),bibid)
                    else:
                        for oclcnum in d[1:]:
                            self.add_oclcnum_to_bibid(int(oclcnum),bibid)
        fh.close()
        logging.warning("read %d lines from %s" % (n,file))

    def add_oclcnum_to_bibid(self,oclcnum,bibid):
        """Add mapping of oclcnum to bibid

        Deal with the case that a single oclcnum might map to more
        than one bibid.
        """
        if (oclcnum not in self.bibids):
            self.bibids[oclcnum]=set()
        self.bibids[oclcnum].add(bibid)

    def add_work(self,oclcnum,bibid,workid):
        """Add record of bibid being example of workid

        If self.write_workid_bibids is true then build data structure of
        workid -> bibids.

        Else, simple write out "workid bibid" pair as it is
        found to avoid using huge memnory.
        """
        if (self.write_workid_bibids):
            if (workid in self.works):
                # Add to list, already have one entry
                self.works[workid].append(bibid)
            else:
                # First bibid for this work
                self.works[workid]=[bibid]
        if (self.write_oclcnum_workid_pairs):
            self.oclccn2oclcwn.add("%d,%d" % (oclcnum,workid))
        if (self.write_pairs):
            # Write out matches as we find them to avoid
            # building everything in memory
            self.ofh.write("%d %s\n" % (workid,bibid))

    def write_workid_to_bibid_data(self,file):
        """Write out OCLC workid to bibid mappings
        
        Write comment line to start. Other lines are workid followed by
        one or more bibids.
        """
        fh = gzip.open(file,'w')
        fh.write("#workid bibids\n")
        n = 0
        for workid in sorted(self.works):
            n += 1
            fh.write("%d %s\n" % (workid," ".join([str(x) for x in self.works[workid]])))
        fh.close()
        logging.warning("written %d lines to %s" % (n,file))

    def write_oclccn2oclcwn(self,file):
        """Write cvs format OCLC number, OCLC work number pairs

        Uses same format at Darren's output for Stanford
        """
        fh = gzip.open(file,'w')
        #fh.write("#oclccn,oclcwns\n")
        n = 0
        for pair in sorted(self.oclccn2oclcwn):
            n += 1
            fh.write(pair + "\n")
        fh.close()
        logging.warning("written %d lines to %s" % (n,file))

    def close(self):
        """Close running output file if open"""
        if (self.write_pairs): 
            self.ofh.close()

# Options and arguments
LOGFILE = "mx_get_oclc_workids.log"
p = optparse.OptionParser(description='Find OCLC workids for bibids given bibid-oclcnum and oclcnum-workid data',
                          usage='usage: %prog [bibid_to_oclcnums.gz] [oclc_concordance.gz]')
p.add_option('--write-workid-bibids', action='store', default=None,
             help="Build in-memory data to write workid->bibids mappings to given file.gz")
p.add_option('--write-oclcnum-workid-pairs', action='store', default=None,
             help="Build in-memory data to write oclcnum,workid pairs to given file.gz")
p.add_option('--write-pairs', action='store', default=None,
             help="Write bibid->oclcworkid pairs as oclc data is read (cheap on memory) to given file.gz")
p.add_option('--first-oclcnum-only', action='store_true',
             help="Take only the first OCLC number listed for each bibid")
p.add_option('--logfile', action='store', default=LOGFILE,
             help="Log file name (default %s)" % (LOGFILE))
p.add_option('--dupeslog', action='store', default=None,
             help="Write log for duplicate data")
p.add_option('--verbose', '-v', action='store_true',
             help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

if (len(args)!=2):
    sys.stderr.write('Error - Must have 2 arguments\n\n')
    p.print_help()
    exit(1)
(bibid_to_oclcnums_file,oclc_concordance_file)=args

level = (logging.INFO if opt.verbose else logging.WARNING)
logging.basicConfig(filename=opt.logfile,level=level)
logging.warning("STARTED at %s" % (datetime.datetime.now()))

dupeslog = None
if (opt.dupeslog):
    dupeslog = logging.getLogger(name='dupeslog')
    f = logging.FileHandler(filename=opt.dupeslog,mode='w')
    dupeslog.addHandler(f)
    dupeslog.warning("#DUPES LOG STARTED at %s" % (datetime.datetime.now()))

# Read bibid--oclcnum data into memory
bo = bibid_oclcnums(file=bibid_to_oclcnums_file,
                    dupeslog=dupeslog, 
                    first_oclcnum_only=opt.first_oclcnum_only,
                    write_workid_bibids=(opt.write_workid_bibids is not None),
                    write_oclcnum_workid_pairs=(opt.write_oclcnum_workid_pairs is not None),
                    write_pairs=opt.write_pairs)
logging.warning("Have %d bibid to oclcnum mappings" % (len(bo.bibids.keys())))

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
logging.warning("READING CONCORDANCE at %s" % (datetime.datetime.now()))
fh = gzip.open(oclc_concordance_file,'r')
n = 0
num1_matches = 0
num2_matches = 0
num_none_workid = 0
for line in fh:
    n += 1
    if (n%1000000 == 0):
        logging.warning("read %d lines from %s...." % (n,oclc_concordance_file))
    line = line.rstrip()
    try:
        # oclcnum2 is the currently in-use OCLC crontol number and
        # is the one to record. A match on oclcnum1, which may be
        # a previously used number, should be recorded with oclcnum2
        (oclcnum1,oclcnum2,workid) = line.split()
        if (workid=='NONE'):
            num_none_workid += 1
            continue
        oclcnum1=int(oclcnum1)
        oclcnum2=int(oclcnum2)
        workid=int(workid)
        if (oclcnum2 in bo.bibids):
            for bibid in bo.bibids[oclcnum2]:
                bo.add_work(oclcnum2,bibid,workid)
            num2_matches += 1
        elif (oclcnum1 in bo.bibids):
            for bibid in bo.bibids[oclcnum1]:
                bo.add_work(oclcnum2,bibid,workid)
            num1_matches += 1
    except Exception as e:
        logging.warning("[line %d] BAD LINE '%s': %s" % (n,line,str(e)))
fh.close()
logging.warning("read %d lines from %s. %d matches in col2, %d in col1" % (n,oclc_concordance_file,num1_matches,num2_matches))
logging.warning("ignored %d lines that have workid=NONE" % (num_none_workid))

if (opt.write_workid_bibids is not None):
    bo.write_workid_to_bibid_data(opt.write_workid_bibids)
if (opt.write_oclcnum_workid_pairs is not None):
    bo.write_oclccn2oclcwn(opt.write_oclcnum_workid_pairs)
logging.warning("FINISHED at %s" % (datetime.datetime.now()))
bo.close()
