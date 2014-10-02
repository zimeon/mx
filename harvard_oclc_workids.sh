# Harvard catalog data is public and is described at
# http://openmetadata.lib.harvard.edu/bibdata
# (best to grab with 'wget -c http://openmetadata.lib.harvard.edu/bibdata/data'
# to allow painless restart)
#
# Have data in harvard_marc21:
#sw272@sw272-dev harvard_marc21>ls ab*gz
#ab.bib.00.20140919.full.mrc.gzab.bib.08.20140919.full.mrc.gz
#ab.bib.01.20140919.full.mrc.gzab.bib.09.20140919.full.mrc.gz
#ab.bib.02.20140919.full.mrc.gzab.bib.10.20140919.full.mrc.gz
#ab.bib.03.20140919.full.mrc.gzab.bib.11.20140919.full.mrc.gz
#ab.bib.04.20140919.full.mrc.gzab.bib.12.20140919.full.mrc.gz
#ab.bib.05.20140919.full.mrc.gzab.bib.13.20140919.full.mrc.gz
#ab.bib.06.20140919.full.mrc.gzab.bib.14.20140919.full.mrc.gz
#ab.bib.07.20140919.full.mrc.gz
#
# The Harvard bibids has a checksum appended as hyphen-[digit|X], e.g.
# 004082147-1
# 004082148-X
#
# Harvard data appears to include various invalid UTF8 sequences/chars
# and so pymarc will not read it. Ran all files through 
# utf8conditioner which "corrupts" the data by doing dumb substitutions
# but at least makes the rest valid UTF8
#
# sw272@sw272-dev mx>for f in $( ls harvard_marc21/ab*gz ); do zcat $f | ~/src/utf8conditioner/utf8conditioner | gzip -c > $f.new ; done
# ....check files....
# w272@sw272-dev mx>for f in $( ls harvard_marc21/ab*gz ); do mv $f.new $f ; done
#
# Run all processes to extract OCLC references from MARCXML
# records, match these against OCLC concordance file,
# and then group by workid
#
# 1. extract 035$a refs to OCLC nums
rm -f harvard/bibid_to_oclcnums.log harvard/bibid_to_oclcnums_dupes.log
./mx_grep_oclc.py -v --logfile harvard/bibid_to_oclcnums.log --dupeslog harvard/bibid_to_oclcnums_dupes.log harvard_marc21/ab*.gz | gzip -c > harvard/bibid_to_oclcnums.dat.gz
#
# 2. match up with OCLC concordance to get work ids
#rm -f harvard/workid_bibid_pairs.log harvard/workid_bibid_pair_dupes.log
#./mx_get_oclc_workids.py -v --logfile harvard/workid_bibid_pairs.log --dupeslog harvard/workid_bibid_pair_dupes.log harvard/bibid_to_oclcnums.dat.gz oclcnum_workid_concordance.txt.gz harvard/workid_bibid_pairs.dat.gz
#
# 3. got though workid-bibid pairs to group by workid and get some stats
#rm -f harvard/workid_bibids.log 
#./mx_analyze_workids.py --logfile harvard/workid_bibids.log harvard/workid_bibid_pairs.dat.gz harvard/workid_bibids.dat.gz