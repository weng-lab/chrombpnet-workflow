import krews.core.*
import krews.file.File
import krews.run
import reactor.core.publisher.toFlux
import task.*
import model.*

fun main(args: Array<String>) = run(chromBPNetWorkflow, args)

data class ChromBPNetParams(
    val inputs: List<ChromBPNetInput>
)

val chromBPNetWorkflow = workflow("chrombpnet-workflow") {

    val params = params<ChromBPNetParams>()
    val inputs = params.inputs
        .filter { it.trainedModel == null }
        .map { TrainTaskInput(it) }
        .toFlux()
    val preTrainedInputs = params.inputs
        .filter { it.trainedModel != null }

    // train any models which are not yet trained
    val trainingOutputs = trainTask("train", inputs)

    // run prediction of signal profiles
    predictionTask(
        "predict",
        trainingOutputs
            .map {
                PredictionTaskInput(
                    name = it.name,
                    chromBPNetModelH5 = it.chromBPNetModelH5,
                    chromBPNetModelBiasCorrectedH5 = it.chromBPNetModelBiasCorrectedH5,
                    chromBPNetModelBiasScaledH5 = it.chromBPNetModelBiasScaledH5,
                    evaluationRegions = it.evaluationRegions
                )
            }
            .concatWith(
                preTrainedInputs
                    .map {
                        PredictionTaskInput(
                            name = it.name,
                            chromBPNetModelH5 = it.trainedModel!!.chromBPNetModelH5,
                            chromBPNetModelBiasCorrectedH5 = it.trainedModel.chromBPNetModelBiasCorrectedH5,
                            chromBPNetModelBiasScaledH5 = it.trainedModel.chromBPNetModelBiasScaledH5,
                            evaluationRegions = it.evaluationRegions
                        )
                    }
                    .toFlux()
            )
    )

    // split outputs for parallelization of shap score computation
    val splitOutput = splitTask(
        "split",
        trainingOutputs
            .map {
                SplitTaskInput(
                    name = it.name,
                    modelH5 = it.chromBPNetModelBiasCorrectedH5,
                    input = it.evaluationRegions
                )
            }
            .concatWith(
                preTrainedInputs
                    .map {
                        SplitTaskInput(
                            name = it.name,
                            modelH5 = it.trainedModel!!.chromBPNetModelBiasCorrectedH5,
                            input = it.evaluationRegions
                        )
                    }
                    .toFlux()
            )
    )

    // compute profile and count importance scores
    val shapOutput = shapTask(
        "shap",
        splitOutput
            .flatMap {
                it.pieces.mapIndexed { i, v ->
                    ShapTaskInput(
                        name = it.name,
                        modelH5 = it.modelH5,
                        index = i,
                        piece = v
                    )
                }.toFlux()
            }
    )

    // merge profile count and importance scores together from the pieces
    mergeTask(
        "merge",
        shapOutput
            .groupBy { it.name }
            .flatMap { group ->
                group
                    .map { output -> 
                        Pair(output.profileScoreBW, output.countScoreBW)
                    }
                    .collectList()
                    .map { pairList -> 
                        MergeTaskInput(
                            name = group.key()!!,
                            profilePieces = pairList.map { it.first },
                            countPieces = pairList.map { it.second }
                        )
                    }
            }
    )

}