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
    val chromBPNetModelH5: File,
    val chromBPNetModelBiasCorrectedH5: File,
    val chromBPNetModelBiasScaledH5: File
)
