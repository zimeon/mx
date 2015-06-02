# Cornell University Library (CUL) analysis

Files in this directory are build with the script <../cul_oclc_workids.sh> from 2 input datasets (neither of which is included in github because of size):

  # `bib.xml.full/*` (~26GB) which is the set of 7M MARCXML bib records for CUL
  # `oclcnum_workid_concordance.txt.gz` (~3GB, 343M lines) which is concordance data from OCLC mapping OCLC numbers (for bib records) to OCLC work ids

Steps of the analysis are outlined below:

## 1. Extract OCLC numbers from CUL MARCXML

```
./mx_grep_oclc.py -v --logfile cul/bibid_to_oclcnums.log --dupeslog cul/bibid_to_oclcnums_dupes.log bib.xml.full/bib.*.xml.gz | gzip -c > cul/bibid_to_oclcnums.dat.gz
```

output files are:

  * bibid_to_oclcnums.dat.gz - CUL bibid to OCLC number mappings
  * bibid_to_oclcnums.log - General log, includes bad numbers
  * bibid_to_oclcnums_dupes.log - Log of cases where we have an OCLC number that appears in more than one record or more than once in a records (these are not included in the output data)

## 2. Find relevant mappings from OCLC numbers to OCLC work ids

Based on the OCLC numbers in the mapping from CUL bibids to OCLC numbers from step 1, use the OCLC concordance data to pull out all the OCLC number to workid pairs relevant to CUL.

```
./mx_get_oclc_workids.py --write-oclcnum-workid-pairs=cul/oclcnum_workid_pairs.csv.gz cul/bibid_to_oclcnums.dat.gz oclcnum_workid_concordance.txt.gz
```

output file:

  * [oclcnum_workid_pairs.csv.gz] - OCLC number -> workid mappings, one per line

## 3. Find OCLC work ids for CUL data



## 4. Go through the workid-bibid pairs to get some stats and join on workid

```
./mx_analyze_workids.py --logfile cul/workid_bibids.log cul/workid_bibid_pairs.dat.gz cul/workid_bibids.dat.gz
```