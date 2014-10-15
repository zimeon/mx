# Harvard Catalog Data

## Where to look in MARC for OCLC master nums at Harvard

_Comments from Paul Deschner, 2014-10_

  * Bib records
     * 035 field, subfield a
     * Local Harvard practice: first indicator
       1. 0: OCLC master record
       2. 1: RLIN record
       3. 2: OCLC institutional record
       4. blank: undefined
  * Holdings records
     * 079 field
     * Tracked in pairs of OCLC master and institutional records (same first indicator values as with bib’s 035)
     * 079’s master records track with bib’s 035 subfield a’s master records: no need to use holding’s 079 data here
