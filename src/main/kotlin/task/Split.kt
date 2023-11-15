package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import org.reactivestreams.Publisher

data class SplitTaskParameters(
    val chunks: Int = 10
)

data class SplitTaskInput(
    val name: String,
    val input: File,
    val modelH5: File,
    val species: String
)

data class SplitTaskOutput(
    val name: String,
    val pieces: List<File>,
    val modelH5: File,
    val species: String
)

fun convertToSplitIndex(num: Int): String {
    val firstChar = 'a' + (num / 26)
    val secondChar = 'a' + (num % 26)
    return "$firstChar$secondChar"
}

fun WorkflowBuilder.splitTask(name: String, i: Publisher<SplitTaskInput>) = this.task<SplitTaskInput, SplitTaskOutput>(name, i) {
    val params = taskParams<SplitTaskParameters>()
    dockerImage = "ubuntu:latest"

    output =
        SplitTaskOutput(
            name = input.name,
            pieces = (0 until params.chunks).map { OutputFile("piece_${input.name}_${convertToSplitIndex(it)}") },
            modelH5 = input.modelH5,
	    species = input.species
        )

    command =
        """
        split -l $(( $(wc -l < ${input.input.dockerPath}) / ${params.chunks} )) ${input.input.dockerPath} $outputsDir/piece_${input.name}_
        """
}
