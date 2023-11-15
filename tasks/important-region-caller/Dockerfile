FROM ubuntu:22.04

RUN apt-get -y update && apt-get -y install python3 python3-pip wget libkrb5-dev libcurl4-openssl-dev && \
    python3 -m pip install pyBigWig numpy hmmlearn && \
    apt-get autoremove -y && \
    apt-get autoclean -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local/genome && \
    wget http://gcp.wenglab.org/hg38.chrom.sizes -O /usr/local/genome/hg38.chrom.sizes && \
    wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/bedToBigBed -O /bin/bedToBigBed && \
    chmod +x /bin/bedToBigBed

COPY important-region-caller.py /bin
COPY find-regions-with-signal.py /bin
RUN chmod +x /bin/important-region-caller.py
RUN chmod +x /bin/find-regions-with-signal.py
