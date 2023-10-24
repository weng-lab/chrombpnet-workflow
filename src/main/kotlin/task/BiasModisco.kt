package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.*
import org.reactivestreams.Publisher

data class BiasModiscoTaskParameters(
    val biasThreshold: Float = 0.5F
)

data class BiasModiscoTaskInput(
    val input: TrainBiasTaskOutput
)

data class BiasModiscoTaskOutput(
    val name: String,    
    val output: OutputDirectory
)

fun WorkflowBuilder.biasModiscoTask(name: String, i: Publisher<BiasModiscoTaskInput>) = this.task<BiasModiscoTaskInput, BiasModiscoTaskOutput>(name, i) {
    val params = taskParams<BiasModiscoTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        BiasModiscoTaskOutput(
            name = input.input.name,
            output = OutputDirectory("bias-evaluation")
        )

    command =
        """
        modisco.py \
            bias \
            ${input.input.biasProfileScores} \
            $outputsDir/bias-evaluation/modisco_profile/profile.h5 \
            ${input.input.biasCountsScores} \
            $outputsDir/bias-evaluation/modisco_counts/counts.h5 \
            $outputsDir
        """
}
