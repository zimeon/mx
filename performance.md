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
```
