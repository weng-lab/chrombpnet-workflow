package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import org.reactivestreams.Publisher

data class TrainTaskParameters(
    val biasThreshold: Float = 0.5F
)

data class TrainTaskInput(
    val input: ChromBPNetInput
)

data class TrainTaskOutput(
    val name: String,
    val biasDirectory: OutputDirectory,
    val modelDirectory: OutputDirectory,
    val biasModelH5: File,
    val chromBPNetModelH5: File,
    val chromBPNetModelBiasCorrectedH5: File,
    val chromBPNetModelBiasScaledH5: File,
    val evaluationRegions: File
)

fun WorkflowBuilder.trainTask(name: String, i: Publisher<TrainTaskInput>) = this.task<TrainTaskInput, TrainTaskOutput>(name, i) {
    val params = taskParams<TrainTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        TrainTaskOutput(
            name = input.input.name,
            modelDirectory = OutputDirectory("model_${input.input.name}"),
            biasDirectory = OutputDirectory("bias_${input.input.name}"),
            biasModelH5 = OutputFile("bias_${input.input.name}/models/bias.h5"),
            chromBPNetModelH5 = OutputFile("model_${input.input.name}/models/chrombpnet.h5"),
            chromBPNetModelBiasCorrectedH5 = OutputFile("model_${input.input.name}/models/chrombpnet_nobias.h5"),
            chromBPNetModelBiasScaledH5 = OutputFile("model_${input.input.name}/models/bias_model_scaled.h5"),
            evaluationRegions = input.input.evaluationRegions
        )

    val bamPaths = input.input.bams.map { it.dockerPath }
    command =
        """
        run-human.py \
            --bams ${bamPaths.joinToString(separator = " ")} \
            --model_output_directory $outputsDir/model_${input.input.name} \
            --bias_output_directory $outputsDir/bias_${input.input.name}
        """
}