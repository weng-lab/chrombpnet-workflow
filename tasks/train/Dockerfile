FROM pratth/chrombpnet:latest

RUN apt-get -y update && apt-get -y install libcairo2-dev libsdl-pango-dev

RUN mkdir -p /usr/local/genome && \
    wget http://gcp.wenglab.org/hg38.2bit -O /usr/local/genome/hg38.2bit && \
    wget http://gcp.wenglab.org/hg38.chrom.sizes -O /usr/local/genome/hg38.chrom.sizes && \
    wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/twoBitToFa -O /bin/twoBitToFa && \
    chmod +x /bin/twoBitToFa && \
    pip install pysam

RUN wget http://gcp.wenglab.org/GRCh38-Anchors.bed.gz -O /usr/local/genome/GRCh38-Anchors.bed.gz

COPY run-human.py /bin
COPY initialize.py /bin
COPY modisco.py /bin
COPY bed3-to-narrowpeak.py /bin
COPY fold.json /usr/local/genome
COPY combinedbams.py /bin
COPY zscores.py /bin
COPY combinedfragments.py /bin
COPY pipelines.py /scratch/chrombpnet/chrombpnet/pipelines.py
RUN chmod -R 777 /usr/local/genome

RUN apt-get autoremove -y && \
    apt-get autoclean -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
