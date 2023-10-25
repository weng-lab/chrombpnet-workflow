package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.*
import org.reactivestreams.Publisher

data class ModelModiscoTaskParameters(
    val biasThreshold: Float = 0.5F
)

data class ModelModiscoTaskInput(
    val input: TrainModelTaskOutput
)

data class ModelModiscoTaskOutput(
    val name: String,    
    val output: OutputDirectory
)

fun WorkflowBuilder.modelModiscoTask(name: String, i: Publisher<ModelModiscoTaskInput>) = this.task<ModelModiscoTaskInput, ModelModiscoTaskOutput>(name, i) {
    val params = taskParams<ModelModiscoTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/chrombpnet:latest"

    output =
        ModelModiscoTaskOutput(
            name = input.input.name,
            output = OutputDirectory("model-evaluation")
        )

    command =
        """
        modisco.py \
            model \
            model \
            ${input.input.noBiasProfileScoresH5.dockerPath} \
            $outputsDir/model-evaluation/modisco_profile/profile.h5 \
            $outputsDir
        """
}
