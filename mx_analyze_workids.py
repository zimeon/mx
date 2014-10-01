#!/usr/bin/env python
#
# Look at workid--bibid pairs and generate a set of
# workid--bibids sets. Look for bibids that are mapped
# to more than one workid.
#
# Simeon Warner - 2014-09-25
#
import gzip
import re
import optparse
import logging
import datetime

WORKID_PREFIX = "http://worldcat.org/entity/work/id/"
BIBID_PREFIX = "http://newcatalog.library.cornell.edu/catalog/"

class workids(object):

    def __init__(self,file=None):
        self.workids={}
        self.bibids={}
        # Read data if specified
        if (file):
            self.read(file)
            
    def read(self,file):
        """Read in workid to bibid pairs into combined workids hash

        Ignores lines starting # and blank lines. Converts all values
        to integers.
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
                elif (len(d)>2):
                    logging.info("[%d] more than two (%d) elements for bibid %s, ignoring" % (n,(len(d)-2),d[0]))
                workid = None
                bibid = None
                # sanity check
                try:
                    workid = int(d[0])
                    bibid = int(d[1])
                except Exception as e:
                    logging.warning("[%d] bad line '%s', ignored" % (n,line))
                    continue
                if (workid in self.workids):
                    self.workids[workid].append(bibid)
                else:
                    self.workids[workid]=[bibid]
                # Look for dupes
                if (bibid in self.bibids):
                    # We expect many dupe pairs, look for the special
                    # case of same bibid with different workids
                    if (workid not in self.bibids[bibid]):
                        self.bibids[bibid].append(workid)
                        logging.warning("Dupe: bibid %d attached to multiple workids [%s]" % (bibid,",".join([str(x) for x in self.bibids[bibid]])))
                else:
                    self.bibids[bibid]=[workid]
        fh.close()
        logging.warning("read %d lines from %s, have %d works" % (n,file,len(self.workids)))

    def write_works_data(self,file):
        """Write out OCLC workid to bibid mappings
        
        Write comment line to start. Other lines are workid followed by
        one or more bibids.
        """
        fh = gzip.open(file,'w')
        fh.write("#workid bibids\n")
        fh.write("#prefix workid with %s to get URI\n" % (WORKID_PREFIX))
        fh.write("#prefix bibids with %s to get URI\n" % (BIBID_PREFIX))
        n = 0
        for workid in sorted(self.workids.keys(),key=int):
            n += 1
            fh.write("%d %s\n" % (workid," ".join([str(x) for x in self.workids[workid]])))
        fh.close()
        logging.warning("written %d workid lines to %s" % (n,file))

    def stats(self):
        """Simple descriptive stats for the workid associations
        
        Output via logger
        """
        counts={}
        example={}
        for workid in self.workids:
            n=len(self.workids[workid])
            if (n in counts):
                counts[n] += 1
            else:
                counts[n] = 1
                # Add first case as example, add first 3 (at most) bibid links
                biblinks = ["%s%d" % (BIBID_PREFIX,x) for x in self.workids[workid][0:2]]
                example[n] = "%s%d -> %s" % (WORKID_PREFIX,workid,' '.join(biblinks)) 
        # output histogram data
        logging.warning("histogram: #num_bibids workids_with_num_bibids (example)")
        for n in sorted(counts):
            logging.warning("histogram: %d %d" % (n,counts[n]))
            logging.warning("histogram_eg: %s" % (example[n]))


# Options and arguments
LOGFILE = 'mx_analyze_workids.log'
p = optparse.OptionParser(description='Combine and analyze workid to bibid pairs',
                          usage='usage: %prog [workid_bibid_pairs_in.gz] [workid_bibids_out.gz]')
p.add_option('--logfile', action='store', default=LOGFILE,
             help="Log file name (default %s)" % (LOGFILE))
p.add_option('--verbose', '-v', action='store_true',
              help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

if (len(args)!=2):
    p.print_help()
    exit(1)
(workid_bibid_pairs,workid_bibids)=args

level = logging.INFO if (opt.verbose) else logging.WARNING
logging.basicConfig(filename=opt.logfile, level=level)
logging.warning("STARTED at %s" % (datetime.datetime.now()))

# Read bibid--oclcnum data into memory
w = workids(workid_bibid_pairs)
logging.info("Have %d workids, %d bibids" % (len(w.workids),len(w.bibids)))

# Write out combined works data and stats
w.write_works_data(workid_bibids)
w.stats()

logging.warning("FINISHED at %s" % (datetime.datetime.now()))
