package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import org.reactivestreams.Publisher

data class PredictionNumpyTaskParameters(
    val tqdm: Int = 1
)

data class PredictionNumpyTaskInput(
    val name: String,
    val chromBPNetModelH5: File,
    val chromBPNetModelBiasCorrectedH5: File,
    val chromBPNetModelBiasScaledH5: File,
    val evaluationRegions: File,
    val sequence: File? = null
)

data class PredictionNumpyTaskOutput(
    val name: String,
    val chromBPNetProfilePredictions: File,
    val chromBPNetCountPredictions: File
)

fun WorkflowBuilder.predictionNumpyTask(name: String, i: Publisher<PredictionNumpyTaskInput>) = this.task<PredictionNumpyTaskInput, PredictionNumpyTaskOutput>(name, i) {
    val params = taskParams<PredictionNumpyTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet-prediction:latest"

    output =
        PredictionNumpyTaskOutput(
            name = input.name,
            chromBPNetProfilePredictions = OutputFile("predictions_${input.name}.profile.npy"),
            chromBPNetCountPredictions = OutputFile("predictions_${input.name}.counts.npy")
        )

    command =
        """
        twoBitToFa ${input.sequence?.dockerPath ?: "/usr/local/genome/hg38.2bit"} /tmp/sequence.fa && \
        predict.py \
            /tmp/sequence.fa \
            ${input.evaluationRegions.dockerPath} \
            ${input.chromBPNetModelH5.dockerPath} \
            $outputsDir/predictions_${input.name}.profile.npy \
            $outputsDir/predictions_${input.name}.counts.npy
        """
}
