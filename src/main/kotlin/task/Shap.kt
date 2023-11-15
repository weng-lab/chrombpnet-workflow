package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import model.ASSEMBLIES
import org.reactivestreams.Publisher

data class ShapTaskParameters(
    val tqdm: Int = 1
)

data class ShapTaskInput(
    val name: String,
    val index: Int,
    val piece: File,
    val modelH5: File,
    val species: String
)

data class ShapTaskOutput(
    val name: String,
    val profileScoreBW: File,
    val countScoreBW: File
)

fun WorkflowBuilder.shapTask(name: String, i: Publisher<ShapTaskInput>) = this.task<ShapTaskInput, ShapTaskOutput>(name, i) {
    val params = taskParams<ShapTaskParameters>()
    val assembly = ASSEMBLIES.get(input.species)
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        ShapTaskOutput(
            name = input.name,
            countScoreBW = OutputFile("${input.name}.${input.index}.counts_scores.bw"),
            profileScoreBW = OutputFile("${input.name}.${input.index}.profile_scores.bw")
        )

    command =
        """
        twoBitToFa /usr/local/genome/$assembly.2bit /tmp/$assembly.fa && \
        bed3-to-narrowpeak.py ${input.piece.dockerPath} /tmp/regions.narrowPeak && \
        chrombpnet contribs_bw \
            --model-h5 ${input.modelH5.dockerPath} \
            --regions /tmp/regions.narrowPeak \
            --genome /tmp/$assembly.fa \
            --chrom-sizes /usr/local/genome/$assembly.chrom.sizes \
            --output-prefix $outputsDir/${input.name}.${input.index} \
            --tqdm ${params.tqdm}
        """
}
