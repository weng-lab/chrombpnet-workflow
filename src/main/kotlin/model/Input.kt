package model
import krews.file.File

interface ChromBPNetInput {
    val name: String
    val evaluationRegions: File
    val trainedModel: TrainedModelInput?
}

data class ChromBPNetBAMInput(
    override val name: String,
    val bams: List<File>,
    override val evaluationRegions: File,
    override val trainedModel: TrainedModelInput? = null
) : ChromBPNetInput

data class ChromBPNetFragmentFileInput(
    override val name: String,
    val fragmentFiles: List<File>,
    override val evaluationRegions: File,
    val barcodeFile: File? = null,
    override val trainedModel: TrainedModelInput? = null
) : ChromBPNetInput

data class TrainedModelInput(
    val biasModelH5: File,
    val chromBPNetModelH5: File? = null,
    val chromBPNetModelBiasCorrectedH5: File? = null,
    val chromBPNetModelBiasScaledH5: File? = null
)

fun TrainedModelInput.hasCompleteModel(): Boolean {
    return chromBPNetModelH5?.let { true } ?: false &&
           chromBPNetModelBiasCorrectedH5?.let { true } ?: false &&
           chromBPNetModelBiasScaledH5?.let { true } ?: false
}
