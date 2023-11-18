package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import org.reactivestreams.Publisher

data class MergeTaskParameters(
    val tqdm: Int = 1,
    val assembly: String? = "hg38"
)

data class MergeTaskInput(
    val name: String,
    val profilePieces: List<File>,
    val countPieces: List<File>
)

data class MergeTaskOutput(
    val name: String,
    val profileBigWig: File,
    val countBigWig: File
)

fun WorkflowBuilder.mergeTask(name: String, i: Publisher<MergeTaskInput>) = this.task<MergeTaskInput, MergeTaskOutput>(name, i) {
    val params = taskParams<MergeTaskParameters>()
    dockerImage = "gcr.io/devenv-215523/big-wig-merge:latest"

    output =
        MergeTaskOutput(
            name = input.name,
            profileBigWig = OutputFile("${input.name}.profile_scores.bw"),
            countBigWig = OutputFile("${input.name}.count_scores.bw")
        )

    val profileBwPaths = input.profilePieces.map { it.dockerPath }
    val countBwPaths = input.countPieces.map { it.dockerPath }
    command =
        """
        merge.py ${params.assembly} $outputsDir/${input.name}.profile_scores.bw ${profileBwPaths.joinToString(separator = " ")} && \
        merge.py ${params.assembly} $outputsDir/${input.name}.count_scores.bw ${countBwPaths.joinToString(separator = " ")}
        """
}
