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


class workids(object):

    def __init__(self,file=None):
        self.workids={}
        self.bibids={}
        # Read data if specified
        if (file):
            self.read(file)
            
    def read(self,file):
        """Read in workid to bibid pairs into combined workids hash

        Ignores lines starting # and blank lines
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
                (workid,bibid) = d
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
                        logging.warning("Dupe: bibid %s attached to self.workids [%s]" % (bibid,",".join(self.bibids[bibid])))
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
        fh.write("#prefix workid with http://worldcat.org/entity/work/id/ to get URI\n")
        fh.write("#prefix bibids with http://newcatalog.library.cornell.edu/catalog/ to get URI\n")
        n = 0
        for workid in sorted(self.works):
            n += 1
            fh.write("%s %s\n" % (workid," ".join(self.works[workid])))
        fh.close()
        logging.warning("written %d lines to %s" % (n,file))

# Options and arguments
__version__ = '0.0.1'
p = optparse.OptionParser(description='Combine and analyze workid to bibid pairs',
                          usage='usage: %prog [workid_bibid_pairs.gz] [works_out.gz',
                          version='%prog '+__version__ )
p.add_option('--verbose', '-v', action='store_true',
              help="verbose, show additional informational messages")
(opt, args) = p.parse_args()

if (len(args)!=2):
    p.print_help()
    exit(1)
(workid_bibid_pairs,workid_bibids)=args

if (opt.verbose):
    logging.basicConfig(level=logging.INFO)

# Read bibid--oclcnum data into memory
w = workids(workid_bibid_pairs)
print "Have %d bibid to oclcnum mappings" % (len(w.bibids.keys()))
## Write out combined works data...
w.write_works_data(workid_bibids)

