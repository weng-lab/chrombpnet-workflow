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
    val species: String
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
	    species = input.input.species
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
        = "--bias_model ${input.input.biasModelH5.dockerPath}"
    command =
        """
        run-{input.input.species}.py \
            $inputPaths \
            --model_output_directory $outputsDir/model_${input.input.name} \
            $biasModelFlag \
            $barcodeFlag
        """
}
