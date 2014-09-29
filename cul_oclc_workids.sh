# Run all processes to extract OCLC references from MARCXML
# records, match these against OCLC concordance file,
# and then group by workid
#
# 1. extract 035$a refs to OCLC nums
rm -f cul/bibid_to_oclcnums.log cul/bibid_to_oclcnums_dupes.log
./mx_grep_oclc.py -v --logfile cul/bibid_to_oclcnums.log --dupeslog cul/bibid_to_oclcnums_dupes.log bib.xml.full/bib.*.xml.gz | gzip -c > cul/bibid_to_oclcnums.dat.gz
#
# 2. match up with OCLC concordance to get work ids
rm -f cul/workid_bibid_pairs.log cul/workid_bibid_pair_dupes.log
./mx_get_oclc_workids.py -v --logfile cul/workid_bibid_pairs.log --dupeslog cul/workid_bibid_pair_dupes.log cul/bibid_to_oclcnums.dat.gz oclcnum_workid_concordance.txt.gz cul/workid_bibid_pairs.dat.gz
#
# 3. got though workid-bibid pairs to group by workid and get some stats
