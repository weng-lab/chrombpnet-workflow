FROM ubuntu:latest

RUN apt-get -y update && \
    apt-get -y install bedtools wget libcurl4-openssl-dev python3 python3-pip && \
    python3 -m pip install joblib && \
    wget "https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bedGraphToBigWig" -O /bin/bedGraphToBigWig && \
    wget "https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bigWigToBedGraph" -O /bin/bigWigToBedGraph && \
    chmod +x /bin/bigWigToBedGraph && \
    chmod +x /bin/bedGraphToBigWig && \
    mkdir -p /usr/local/genome && \
    wget http://gcp.wenglab.org/hg38.chrom.sizes -O /usr/local/genome/hg38.chrom.sizes && \
    apt-get -y remove wget python3-pip && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY merge.py /bin
RUN chmod +x /bin/merge.py
