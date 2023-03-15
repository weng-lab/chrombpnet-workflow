package model
import krews.file.File

data class ChromBPNetInput(
    val name: String,
    val bams: List<File>,
    val evaluationRegions: File,
    val trainedModel: TrainedModelInput? = null
)

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
