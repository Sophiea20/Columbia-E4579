from src.recommendation_system.recommendation_flow.candidate_generators.RandomGenerator import (
    RandomGenerator,
)
from src.recommendation_system.recommendation_flow.controllers.AbstractController import (
    AbstractController,
)
from src.recommendation_system.recommendation_flow.filtering.fall_2023.AlphaFilter import (
    AlphaFilter,
)
from src.recommendation_system.recommendation_flow.model_prediction.RandomModel import (
    RandomModel,
)
from src.recommendation_system.recommendation_flow.ranking.RandomRanker import (
    RandomRanker,
)
from src.recommendation_system.recommendation_flow.candidate_generators.alpha.TwoTowerANNGenerator import (
    TwoTowerANNGenerator,
)
from src.recommendation_system.recommendation_flow.candidate_generators.alpha.CollaberativeFilteredSimilarUsersGenerator import (
    CollaberativeFilteredSimilarUsersGenerator,
)
from src.recommendation_system.recommendation_flow.candidate_generators.alpha.YourChoiceGenerator import (
    YourChoiceGenerator,
)

from src.api.metrics.models import TeamName


class AlphaController(AbstractController):
    def get_content_ids(self, user_id, limit, offset, seed, starting_point):
        if seed <= 1:  # MySql seeds should be [0, # of rows] not [0, 1]
            seed *= 1000000
        candidate_limit = 500
        candidates, scores = [], []
        generators = []
        if starting_point.get("twoTower", False):
            generators.append(TwoTowerANNGenerator)
        if starting_point.get("collabFilter", False):
            generators.append(CollaberativeFilteredSimilarUsersGenerator)
        if starting_point.get("yourChoice", False):
            generators.append(YourChoiceGenerator)
        for gen in generators:
            cur_candidates, cur_scores = gen().get_content_ids(
                TeamName.Alpha_F2023,
                user_id,
                candidate_limit,
                offset,
                seed,
                starting_point,
            )
            candidates += cur_candidates
            scores += cur_scores
        filtered_candidates = AlphaFilter().filter_ids(
            TeamName.Alpha_F2023,
            user_id, candidates, seed, starting_point
        )
        if starting_point.get('inverseFilter', False):
            filtered_candidates = set(candidates) - set(filtered_candidates)
        predictions = RandomModel().predict_probabilities(
            filtered_candidates,
            user_id,
            seed=seed,
            scores={
                content_id: {"score": score}
                for content_id, score in zip(candidates, scores)
            }
            if scores is not None
            else {},
        )
        rank = RandomRanker().rank_ids(limit, predictions, seed, starting_point)
        return rank
