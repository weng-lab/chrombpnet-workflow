package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.*
import org.reactivestreams.Publisher

data class TrainBiasTaskParameters(
    val biasThreshold: Float = 0.5F
)

data class TrainBiasTaskInput(
    val input: ChromBPNetInput
)

data class TrainBiasTaskOutput(
    val name: String,
    val biasDirectory: OutputDirectory,
    val biasModelH5: File,
    val evaluationRegions: File,
    val biasProfileScores: File,
    val biasCountsScores: File
)

fun WorkflowBuilder.trainBiasTask(name: String, i: Publisher<TrainBiasTaskInput>) = this.task<TrainBiasTaskInput, TrainBiasTaskOutput>(name, i) {
    val params = taskParams<TrainBiasTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        TrainBiasTaskOutput(
            name = input.input.name,
            biasDirectory = OutputDirectory("bias_${input.input.name}"),
            biasModelH5 = OutputFile("bias_${input.input.name}/models/bias.h5"),
            biasProfileScores = OutputFile("bias_${input.input.name}/auxiliary/interpret_subsample/bias.profile_scores.h5"),
            biasCountsScores = OutputFile("bias_${input.input.name}/auxiliary/interpret_subsample/bias.counts_scores.h5"),
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
        = "--bias_output_directory $outputsDir/bias_${input.input.name}"

    command =
        """
        run-human.py \
            $inputPaths \
            --model_output_directory $outputsDir/model_${input.input.name} \
            $biasModelFlag \
            $barcodeFlag
        """
}
