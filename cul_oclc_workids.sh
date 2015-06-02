# Run all processes to extract OCLC references from MARCXML
# records, match these against OCLC concordance file,
# and then group by workid
#
# 1. extract 035$a refs to OCLC nums
echo
date
echo "Step 1 - Extract OCLC numbers from CUL MARCXML"
rm -f cul/bibid_to_oclcnums.log cul/bibid_to_oclcnums_dupes.log
./mx_grep_oclc.py -v --logfile cul/bibid_to_oclcnums.log --dupeslog cul/bibid_to_oclcnums_dupes.log bib.xml.full/bib.*.xml.gz | gzip -c > cul/bibid_to_oclcnums.dat.gz

# 2. get workid to bibid pairs
echo
date
echo "Step 2 - Find OCLC work ids -> bibid pairs for CUL data"
rm -f cul/workid_bibid_pairs.log
./mx_get_oclc_workids.py -v --logfile cul/workid_bibid_pairs.log --write-pairs cul/workid_bibid_pairs.dat.gz cul/bibid_to_oclcnums.dat.gz oclcnum_workid_concordance.txt.gz

#
# 3. match up bibids with OCLC concordance to get OCLC nums to OCLC work ids
#rm -f cul/oclcnum_workid_pairs.csv.gz 
#./mx_get_oclc_workids.py --logfile cul/oclcnum_workid_pairs.log --write-oclcnum-workid-pairs=cul/oclcnum_workid_pairs.csv.gz cul/bibid_to_oclcnums.dat.gz oclcnum_workid_concordance.txt.gz
#
# 4. match up bibds with OCLC concordance to get bibids to OCLC work ids
#echo
#date
#echo "Step 3 - Find OCLC work ids for CUL data"
#rm -f cul/workid_bibids.log cul/workid_bibid_dupes.log
#./mx_get_oclc_workids.py -v --logfile cul/workid_bibids.log --dupeslog cul/workid_bibids_dupes.log --write-workid-bibids cul/workid_bibids.dat.gz cul/bibid_to_oclcnums.dat.gz oclcnum_workid_concordance.txt.gz

#
# 5. got though workid-bibid pairs to group by workid and get some stats
echo
date
echo "Step 4 - Go through the workid-bibid pairs to get some stats and join on workid"
rm -f cul/workid_bibids2.log 
./mx_analyze_workids.py --logfile cul/workid_bibids2.log cul/workid_bibid_pairs.dat.gz cul/workid_bibids2.dat.gz
#
echo
date
echo "Done"
