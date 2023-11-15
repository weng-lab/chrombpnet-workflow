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
        .filter { !(it is IndividualPredictionInput) }
        .filter { it.trainedModel == null || !(it.trainedModel as TrainedModelInput).hasCompleteModel() }
        .map { TrainBiasTaskInput(it) }
        .toFlux()
    val preTrainedInputs = params.inputs
        .filter { !(it is IndividualPredictionInput) }
        .filter { it.trainedModel?.hasCompleteModel() ?: false }

    // train any models which are not yet trained
    val biasTrainingOutputs = trainBiasTask("train-bias", inputs)
    val trainingOutputs = trainModelTask(
        "train-model",
        biasTrainingOutputs
            .map {
                TrainModelTaskInput(
                    input = it
                )
            }
    )

    // run modisco
    biasModiscoTask(
        "bias-modisco",
        biasTrainingOutputs
            .map {
                BiasModiscoTaskInput(
                    input = it
                )
            }
    )
    modelModiscoTask(
        "model-modisco",
        trainingOutputs
            .map {
                ModelModiscoTaskInput(
                    input = it
                )
            }
    )

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
                            chromBPNetModelH5 = it.trainedModel!!.chromBPNetModelH5!!,
                            chromBPNetModelBiasCorrectedH5 = (it.trainedModel as TrainedModelInput).chromBPNetModelBiasCorrectedH5!!,
                            chromBPNetModelBiasScaledH5 = (it.trainedModel as TrainedModelInput).chromBPNetModelBiasScaledH5!!,
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
                    input = it.evaluationRegions,
		    species = it.species
                )
            }
            .concatWith(
                preTrainedInputs
                    .map {
                        SplitTaskInput(
                            name = it.name,
                            modelH5 = it.trainedModel!!.chromBPNetModelBiasCorrectedH5!!,
                            input = it.evaluationRegions,
			    species = it.species
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
                        piece = v,
			species = it.species
                    )
                }.toFlux()
            }
    )

    // merge profile count and importance scores together from the pieces
    val mergeOutputs = mergeTask(
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

    // run prediction on individually passed sequence/region pairs
    val individualPredictionInputs = params.inputs
        .filter { it is IndividualPredictionInput }
        .flatMap {
            (it as IndividualPredictionInput).models.flatMap { model ->
                it.sequences.map { seq ->
                    PredictionTaskInput(
                        "${it.name}.${model.name}.${seq.name}",
                        model.chromBPNetModelH5,
                        model.chromBPNetModelBiasCorrectedH5,
                        model.chromBPNetModelBiasScaledH5,
                        it.evaluationRegions,
                        seq.file
                    )
                }
            }
        }.toFlux()
    predictionTask(
        "individual-predict",
        individualPredictionInputs
    )

    // run prediction on individually passed sequence/region pairs
    val individualNumpyPredictionInputs = params.inputs
        .filter { it is IndividualPredictionInput }
        .flatMap {
            (it as IndividualPredictionInput).models.flatMap { model ->
                it.sequences.map { seq ->
                    PredictionNumpyTaskInput(
                        "${it.name}.${model.name}.${seq.name}",
                        model.chromBPNetModelH5,
                        model.chromBPNetModelBiasCorrectedH5,
                        model.chromBPNetModelBiasScaledH5,
                        it.evaluationRegions,
                        seq.file
                    )
                }
            }
        }.toFlux()
    predictionNumpyTask(
        "individual-predict-numpy",
        individualNumpyPredictionInputs
    )

}
