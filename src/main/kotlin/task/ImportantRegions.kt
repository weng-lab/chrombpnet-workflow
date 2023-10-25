package task

import krews.core.WorkflowBuilder
import krews.file.*
import krews.file.OutputDirectory
import model.ChromBPNetInput
import org.reactivestreams.Publisher

data class ImportantRegionTaskParameters(
    val threshold: Float = 2.0F
)

data class ImportantRegionTaskInput(
    val name: String,
    val countBigWig: File,
    val profileBigWig: File,
    val regions: File
)

data class ImportantRegionTaskOutput(
    val name: String,
    val countPositiveRegions: File,
    val countNegativeRegions: File,
    val profilePositiveRegions: File,
    val profileNegativeRegions: File
)

fun WorkflowBuilder.importantRegionTask(name: String, i: Publisher<ImportantRegionTaskInput>) = this.task<ImportantRegionTaskInput, ImportantRegionTaskOutput>(name, i) {
    val params = taskParams<ImportantRegionTaskParameters>()
    dockerImage = "/home/henry.pratt-umw/images/important-region-caller_latest.sif"

    output =
        ImportantRegionTaskOutput(
            name = input.name,
            countNegativeRegions = OutputFile("${input.name}.counts.negative-important-regions.bg"),
            countPositiveRegions = OutputFile("${input.name}.counts.positive-important-regions.bg"),
            profileNegativeRegions = OutputFile("${input.name}.profile.negative-important-regions.bg"),
            profilePositiveRegions = OutputFile("${input.name}.profile.positive-important-regions.bg")
        )

    command =
        """
        important-region-caller.py \
            --bigwig ${input.countBigWig.dockerPath} \
            --bed ${input.regions.dockerPath} \
            --positive-output $outputsDir/${input.name}.counts.negative-important-regions.bb \
            --negative-output $outputsDir/${input.name}.counts.positive-important-regions.bb && \
        important-region-caller.py \
            --bigwig ${input.profileBigWig.dockerPath} \
            --bed ${input.regions.dockerPath} \
            --positive-output $outputsDir/${input.name}.profile.negative-important-regions.bb \
            --negative-output $outputsDir/${input.name}.profile.positive-important-regions.bb
        """
}
