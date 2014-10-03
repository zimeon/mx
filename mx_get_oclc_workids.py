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

    def __init__(self,file=None,output_file=None,store_works=False,dupeslog=None,first_oclcnum_only=False):
        # Options
        self.dupeslog=dupeslog
        self.first_oclcnum_only=first_oclcnum_only
        #
        self.bibids={}
        self.store_works=store_works
        if (store_works):
            self.works={}
        # Set up output file
        self.ofh = gzip.open(output_file,'w')
        self.ofh.write("#workid bibid\n")
        self.ofh.write("#prefix workid with http://worldcat.org/entity/work/id/ to get URI\n")
        self.ofh.write("#prefix bibids with http://newcatalog.library.cornell.edu/catalog/ to get URI\n")
        self.ofh.write("#we expect many duplicate lines due to look up based on 001 and 019 OCLC data\n")
        # Read data if specified
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

    def add_work(self,bibid,workid):
        """Add record of bibid being example of workid

        If self.store_works is true then build data structure of
        workid -> bibids.

        Else, simple write out "workid bibid" pair as it is
        found to avoid using huge memnory.
        """
        if (self.store_works):
            if (workid in self.works):
                # Add to list, already have one entry
                self.works[workid].append(bibid)
            else:
                # First bibid for this work
                self.works[workid]=[bibid]
        else:
            # Write out matches as we find them to avoid
            # building everything in memory
            self.ofh.write("%d %s\n" % (workid,bibid))

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
            fh.write("%d %s\n" % (workid," ".join([str(x) for x in self.works[workid]])))
        fh.close()
        logging.warning("written %d lines to %s" % (n,file))

# Options and arguments
LOGFILE = "mx_get_oclc_workids.log"
p = optparse.OptionParser(description='Find OCLC workids for bibids given bibid-oclcnum and oclcnum-workid data',
                          usage='usage: %prog [bibid_to_oclcnums.gz] [oclc_concordance.gz] [works_out.gz]')
p.add_option('--first-oclcnum-only', action='store_true',
             help="Take only the first OCLC number listed for each bibid")
p.add_option('--logfile', action='store', default=LOGFILE,
             help="Log file name (default %s)" % (LOGFILE))
p.add_option('--dupeslog', action='store', default=None,
             help="Write log for duplicate data")
p.add_option('--verbose', '-v', action='store_true',
             help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

if (len(args)!=3):
    p.print_help("Must have 3 arguments")
    exit(1)
(bibid_to_oclcnums_file,oclc_concordance_file,output_file)=args

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
bo = bibid_oclcnums(file=bibid_to_oclcnums_file,output_file=output_file,dupeslog=dupeslog, first_oclcnum_only=opt.first_oclcnum_only)
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
        (oclcnum1,oclcnum2,workid) = line.split()
        if (workid=='NONE'):
            num_none_workid += 1
            continue
        oclcnum1=int(oclcnum1)
        oclcnum2=int(oclcnum2)
        workid=int(workid)
        if (oclcnum1 in bo.bibids):
            for bibid in bo.bibids[oclcnum1]:
                bo.add_work(bibid,workid)
            num1_matches += 1
        elif (oclcnum2 in bo.bibids):
            for bibid in bo.bibids[oclcnum2]:
                bo.add_work(bibid,workid)
            num2_matches += 1
    except Exception as e:
        logging.warning("[line %d] BAD LINE '%s': %s" % (n,line,str(e)))
fh.close()
logging.warning("read %d lines from %s. %d matches in col1, %d in col2" % (n,oclc_concordance_file,num1_matches,num2_matches))
logging.warning("ignored %d lines that have workid=NONE" % (num_none_workid))
## Write out works data...
#bo.write_works_data(args[2])
#writing alread done on single entry basis
bo.ofh.close();
logging.warning("FINISHED at %s" % (datetime.datetime.now()))
