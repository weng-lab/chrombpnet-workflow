package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import org.reactivestreams.Publisher

data class PredictionTaskParameters(
    val tqdm: Int = 1
)

data class PredictionTaskInput(
    val name: String,
    val chromBPNetModelH5: File,
    val chromBPNetModelBiasCorrectedH5: File,
    val chromBPNetModelBiasScaledH5: File,
    val evaluationRegions: File,
    val sequence: File? = null
)

data class PredictionTaskOutput(
    val name: String,
    val biasPredictions: File,
    val chromBPNetPredictions: File,
    val chromBPNetPredictionsBiasCorrected: File
)

fun WorkflowBuilder.predictionTask(name: String, i: Publisher<PredictionTaskInput>) = this.task<PredictionTaskInput, PredictionTaskOutput>(name, i) {
    val params = taskParams<PredictionTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        PredictionTaskOutput(
            name = input.name,
            biasPredictions = OutputFile("predictions_${input.name}_bias.bw"),
            chromBPNetPredictions = OutputFile("predictions_${input.name}_chrombpnet.bw"),
            chromBPNetPredictionsBiasCorrected = OutputFile("predictions_${input.name}_chrombpnet_nobias.bw")
        )

    command =
        """
        twoBitToFa ${input.sequence?.dockerPath ?: "/usr/local/genome/hg38.2bit"} /usr/local/genome/sequence.fa && \
        bed3-to-narrowpeak.py ${input.evaluationRegions.dockerPath} ${input.evaluationRegions.dockerPath}.narrowPeak && \
        chrombpnet pred_bw \
            --bias-model ${input.chromBPNetModelBiasScaledH5.dockerPath} \
            --chrombpnet-model ${input.chromBPNetModelH5.dockerPath} \
            --chrombpnet-model-nb ${input.chromBPNetModelBiasCorrectedH5.dockerPath} \
            --regions ${input.evaluationRegions.dockerPath}.narrowPeak \
            --genome /usr/local/genome/sequence.fa \
            --chrom-sizes /usr/local/genome/hg38.chrom.sizes \
            --output-prefix $outputsDir/predictions_${input.name} \
            --tqdm ${params.tqdm}
        """
}
