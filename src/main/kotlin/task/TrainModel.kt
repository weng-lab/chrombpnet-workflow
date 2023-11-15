package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.*
import org.reactivestreams.Publisher

data class TrainModelTaskParameters(
    val biasThreshold: Float = 0.5F
)

data class TrainModelTaskInput(
    val input: TrainBiasTaskOutput
)

data class TrainModelTaskOutput(
    val name: String,    
    val modelDirectory: OutputDirectory,
    val chromBPNetModelH5: File,
    val chromBPNetModelBiasCorrectedH5: File,
    val chromBPNetModelBiasScaledH5: File,
    val evaluationRegions: File,
    val noBiasProfileScoresH5: File,
    val species: String,
    val biasMetrics: File,
    val log: File,
    val metrics: File,
    val maxBiasResponse: File
)

fun WorkflowBuilder.trainModelTask(name: String, i: Publisher<TrainModelTaskInput>) = this.task<TrainModelTaskInput, TrainModelTaskOutput>(name, i) {
    val params = taskParams<TrainModelTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        TrainModelTaskOutput(
            name = input.input.name,
            modelDirectory = OutputDirectory("model_${input.input.name}"),
            chromBPNetModelH5 = OutputFile("model_${input.input.name}/models/chrombpnet.h5"),
            chromBPNetModelBiasCorrectedH5 = OutputFile("model_${input.input.name}/models/chrombpnet_nobias.h5"),
            chromBPNetModelBiasScaledH5 = OutputFile("model_${input.input.name}/models/bias_model_scaled.h5"),
            noBiasProfileScoresH5 = OutputFile("model_${input.input.name}/auxiliary/interpret_subsample/chrombpnet_nobias.profile_scores.h5"),
            evaluationRegions = input.input.evaluationRegions,
 	    species = input.input.species,
            biasMetrics = OutputFile("model_${input.input.name}/evaluation/bias_metrics.json"),
            log = OutputFile("model_${input.input.name}/logs/chrombpnet.log"),
            metrics = OutputFile("model_${input.input.name}/evaluation/chrombpnet_metrics.json"),
            maxBiasResponse = OutputFile("model_${input.input.name}/evaluation/chrombpnet_nobias_max_bias_resonse.txt")
        )

    val bamLinks
        = if (input.input.rawInput is ChromBPNetBAMInput)
            (input.input.rawInput as ChromBPNetBAMInput).bams.map { it.dockerPath }.map { "ln -s $it /tmp" }.joinToString(" && ")
        else ""
    val inputPaths
        = if (input.input.rawInput is ChromBPNetBAMInput) {
            val tempDir = "/tmp/"
            val bams = (input.input.rawInput as ChromBPNetBAMInput).bams
            val paths = bams.map { bam ->
                val fileName = java.io.File(bam.dockerPath).name
                java.io.File(tempDir, fileName).absolutePath
            }.joinToString(separator = " ")
            "--bams $paths"
          } else {
            val paths = (input.input.rawInput as ChromBPNetFragmentFileInput).fragmentFiles.map { it.dockerPath }.joinToString(separator = " ")
            "--fragment-files $paths"
          }
    val barcodeFlag
        = if (input.input.rawInput is ChromBPNetBAMInput || (input.input.rawInput as ChromBPNetFragmentFileInput).barcodeFile == null)
            ""
          else
            "--barcode-file ${(input.input as ChromBPNetFragmentFileInput).barcodeFile!!.dockerPath}"
    val peaksFlag
        = if (input.input.peaks != null) "--peaks ${input.input.peaks!!.dockerPath}" else ""
    val biasModelFlag
        = "--bias_model ${input.input.biasModelH5.dockerPath}"
    command =
        """
        $bamLinks && \
        run-{input.input.species}.py \
            $inputPaths \
            --model_output_directory $outputsDir/model_${input.input.name} \
            $biasModelFlag \
            $peaksFlag \
            $barcodeFlag
        """
}
