package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import org.reactivestreams.Publisher

data class ShapTaskParameters(
    val tqdm: Int = 1
)

data class ShapTaskInput(
    val name: String,
    val index: Int,
    val piece: File,
    val modelH5: File
)

data class ShapTaskOutput(
    val name: String,
    val profileScoreBW: File,
    val countScoreBW: File
)

fun WorkflowBuilder.shapTask(name: String, i: Publisher<ShapTaskInput>) = this.task<ShapTaskInput, ShapTaskOutput>(name, i) {
    val params = taskParams<ShapTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        ShapTaskOutput(
            name = input.name,
            countScoreBW = OutputFile("${input.name}.${input.index}.counts_scores.bw"),
            profileScoreBW = OutputFile("${input.name}.${input.index}.profile_scores.bw")
        )

    command =
        """
        twoBitToFa /usr/local/genome/hg38.2bit /usr/local/genome/hg38.fa && \
        bed3-to-narrowpeak.py ${input.piece.dockerPath} ${input.piece.dockerPath}.narrowPeak && \
        chrombpnet contribs_bw \
            --model-h5 ${input.modelH5.dockerPath} \
            --regions ${input.piece.dockerPath}.narrowPeak \
            --genome /usr/local/genome/hg38.fa \
            --chrom-sizes /usr/local/genome/hg38.chrom.sizes \
            --output-prefix $outputsDir/${input.name}.${input.index} \
            --tqdm ${params.tqdm}
        """
}
