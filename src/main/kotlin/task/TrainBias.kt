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
    val biasCountsScores: File,
    val species: String,
    val rawInput: ChromBPNetInput,
    val log: File,
    val biasMetrics: File
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
            evaluationRegions = input.input.evaluationRegions,
            species = input.input.species,
            rawInput = input.input,
            log = OutputFile("bias_${input.input.name}/logs/bias.log"),
            biasMetrics = OutputFile("bias_${input.input.name}/evaluation/bias_metrics.json")
        )

    val bamLinks
        = if (input.input is ChromBPNetBAMInput)
            (input.input as ChromBPNetBAMInput).bams.map { it.dockerPath }.map { "ln -s $it /tmp" }.joinToString(" && ")
        else ""
    val inputPaths
        = if (input.input is ChromBPNetBAMInput) {
            val tempDir = "/tmp/"
            val bams = (input.input as ChromBPNetBAMInput).bams
            val paths = bams.map { bam ->
                val fileName = java.io.File(bam.dockerPath).name
                java.io.File(tempDir, fileName).absolutePath
            }.joinToString(separator = " ")
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
        $bamLinks && \
        run-${input.input.species}.py \
            $inputPaths \
            --model_output_directory $outputsDir/model_${input.input.name} \
            $biasModelFlag \
            $barcodeFlag
        """
}
