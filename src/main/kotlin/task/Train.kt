package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.*
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

    val inputPaths
        = if (input.input is ChromBPNetBAMInput) {
            val paths = (input.input as ChromBPNetBAMInput).bams.map { it.dockerPath }.joinToString(separator = " ")
            "--bams $paths"
          } else {
            val paths = (input.input as ChromBPNetFragmentFileInput).fragmentFiles.map { it.dockerPath }.joinToString(separator = " ")
            "--fragment-files $paths"
          }
    val barcodeFlag
        = if (input.input is ChromBPNetBAMInput || (input.input as ChromBPNetFragmentFileInput).barcodeFile == null)
            ""
          else
            "--barcode-file ${(input.input as ChromBPNetFragmentFileInput).barcodeFile!!.dockerPath}"
    val biasModelFlag
        = if (input.input.trainedModel == null)
            "--bias_output_directory $outputsDir/bias_${input.input.name}"
          else
            "--bias_model ${input.input.trainedModel!!.biasModelH5.dockerPath}"
    command =
        """
        run-human.py \
            $inputPaths \
            --model_output_directory $outputsDir/model_${input.input.name} \
            $biasModelFlag \
            $barcodeFlag
        """
}
