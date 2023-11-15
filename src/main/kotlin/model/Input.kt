package model
import krews.file.File

interface ChromBPNetInput {
    val name: String
    val evaluationRegions: File
    val trainedModel: TrainedModelInput?
    val species: String
    val peaks: File?
}

data class ChromBPNetBAMInput(
    override val name: String,
    val bams: List<File>,
    override val evaluationRegions: File,
    override val trainedModel: TrainedModelInput? = null,
    override val species: String = "human",
    override val peaks: File? = null
) : ChromBPNetInput

data class ChromBPNetFragmentFileInput(
    override val name: String,
    val fragmentFiles: List<File>,
    override val evaluationRegions: File,
    val barcodeFile: File? = null,
    override val trainedModel: TrainedModelInput? = null,
    override val species: String = "human",
    override val peaks: File? = null
) : ChromBPNetInput

data class TrainedModelInput(
    val biasModelH5: File,
    val chromBPNetModelH5: File? = null,
    val chromBPNetModelBiasCorrectedH5: File? = null,
    val chromBPNetModelBiasScaledH5: File? = null
)

data class IndividualPredictionSequence(
    val name: String,
    val file: File
)

data class TrainedPredictiveModel(
    val name: String,
    val chromBPNetModelH5: File,
    val chromBPNetModelBiasCorrectedH5: File,
    val chromBPNetModelBiasScaledH5: File
)

data class IndividualPredictionInput(
    override val name: String,
    val models: List<TrainedPredictiveModel>,
    override val evaluationRegions: File,
    val sequences: List<IndividualPredictionSequence>,
    override val trainedModel: TrainedModelInput? = null,
    override val species: String = "human",
    override val peaks: File? = null
) : ChromBPNetInput

fun TrainedModelInput.hasCompleteModel(): Boolean {
    return chromBPNetModelH5?.let { true } ?: false &&
           chromBPNetModelBiasCorrectedH5?.let { true } ?: false &&
           chromBPNetModelBiasScaledH5?.let { true } ?: false
}

val ASSEMBLIES = mapOf("human" to "hg38", "rat" to "rn7", "mouse" to "mm10")
