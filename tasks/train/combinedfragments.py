#!/usr/bin/env python

import os
import gzip
import tempfile

class CombinedFragmentFiles:

    def __init__(self, files, chromosomes, barcodes = None):
        self.files = files
        self.chromosomes = chromosomes
        self.barcodes = barcodes
    
    def __enter__(self):
        self.tempfile = tempfile.NamedTemporaryFile(suffix = ".gz")
        if self.barcodes is not None:
            with open(self.barcodes, 'r') as f:
                barcodes = { x.strip() for x in f }
        with tempfile.NamedTemporaryFile('rt') as f:
            with gzip.open(self.tempfile.name, 'wt') as o:
                os.system(f"zcat {' '.join(self.files)} | sort -k1,1 -k2,2n > {f.name}")
                if barcodes is None:
                    for line in f:
                        if line.split()[0] in self.chromosomes: o.write(line)
                else:
                    for line in f:
                        if line.split()[0] in self.chromosomes and line.split()[-3] in barcodes:
                            o.write(line)
                o.flush()
        return self.tempfile

    def __exit__(self, *_):
        self.tempfile.close()
