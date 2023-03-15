#!/usr/bin/env python

import os
import tempfile
from joblib import Parallel, delayed

class CombinedBAMs:

    def __init__(self, bams, chromosomes):
        self.bams = bams
        self.chromosomes = chromosomes
    
    def __enter__(self):
        self.bam = tempfile.NamedTemporaryFile('rb', suffix='.bam')

        # if there is only one BAM, open it and return
        if len(self.bams) == 1:
            os.system(f"samtools index {self.bams[0]}")
            os.system(f"samtools view -b -F 4 -F 1024 -F 2048 -F 4096 {self.bams[0]} {self.chromosomes} > {self.bam.name}")
            os.system(f"samtools index {self.bam.name}")
            return self.bam
        
        # sort the remaining BAMs, index, and merge
        tempfiles = [tempfile.NamedTemporaryFile(suffix=".bam") for _ in self.bams]
        Parallel(n_jobs=-1)(
            delayed(lambda i, bam: os.system(f"samtools sort -o {i} {bam}") + os.system(f"samtools index {i}"))(tempfiles[i].name, bam)
            for i, bam in enumerate(self.bams)
        )
        with tempfile.NamedTemporaryFile() as b:
            with tempfile.NamedTemporaryFile() as bb:
                os.system(f"samtools cat -o {bb.name} {' '.join([ x.name for x in tempfiles ])}")
                os.system(f"samtools sort -o {b.name} {bb.name}")
            os.system(f"samtools index {b.name}")
            os.system(f"samtools view -b -F 4 -F 1024 -F 2048 -F 4096 {b.name} {self.chromosomes} > {self.bam.name}")
            os.system(f"rm {b.name}.bai")
        os.system(f"samtools index {self.bam.name}")
        for x in tempfiles:
            x.close()
        return self.bam
    
    def __exit__(self, *args):
        self.bam.close()
