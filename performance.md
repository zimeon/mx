# Performance

## Raw data

7M MARCXML records are about 26GB uncompressed as a set of 754 files containing around 10k records each. These are about 2.4GB when gzipped:

```
sw272@sw272-dev ~>du -sh bib.xml.full
2.4G    bib.xml.full
```

Simply running through them to count lines or count record elements takes 3-4mins on CIT VM:

```
sw272@sw272-dev ~>time zcat bib.xml.full/*.gz | wc -l
647640803

real    3m22.958s
user    2m39.330s
sys    0m16.333s

sw272@sw272-dev ~>time zcat bib.xml.full/*.gz | grep -c '<record>'
7068205

real    3m55.027s
user    2m54.296s
sys    0m18.490s
```

and a little _less_ time on my little old 2011 laptop:

```
simeon@RottenApple ~>time zcat bib.xml.full/*.gz | grep -c '<record>'
7068205

real    2m43.793s
user    2m38.834s
sys    0m8.527s 
```

## Reading with pymarc

```
time ~/src/mx/mx_count.py bib.xml.full/*
10000   bib.xml.full/bib.001.1.xml.gz
10000   bib.xml.full/bib.001.2.xml.gz
10000   bib.xml.full/bib.001.3.xml.gz
10000   bib.xml.full/bib.001.4.xml.gz
9964    bib.xml.full/bib.001.5.xml.gz
10000   bib.xml.full/bib.002.1.xml.gz
...
10000   bib.xml.full/bib.173.2.xml.gz
4833    bib.xml.full/bib.173.3.xml.gz
7068205 TOTAL
13441.75user 9.61system 3:47:16elapsed 98%CPU (0avgtext+0avgdata 72288maxresiden
t)k
4542072inputs+56outputs (0major+6024minor)pagefaults 0swaps```

so 3h47 on VM. A bit faster on laptop:

```
simeon@RottenApple ld4lmarc>time ./mx_count.py ~/bib.xml.full/bib.001.*.gz
10000   /Users/simeon/bib.xml.full/bib.001.1.xml.gz
10000   /Users/simeon/bib.xml.full/bib.001.2.xml.gz
10000   /Users/simeon/bib.xml.full/bib.001.3.xml.gz
10000   /Users/simeon/bib.xml.full/bib.001.4.xml.gz
9964    /Users/simeon/bib.xml.full/bib.001.5.xml.gz
49964   TOTAL

real	1m6.900s
user	1m5.213s
sys	0m0.168s
simeon@RottenApple ld4lmarc>dc
3k 7000000 49964 / 66.9 * 60 / p
156.211
60 / p
2.603
```

so that would be 2.6h to parse all of the 7M records.
