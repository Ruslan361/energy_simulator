from __future__ import annotations

from typing import List

from src.models import BaseGenerator, Consumer
from src.optimizers import BaseOptimizer, OptimizationResult


class Simulator:
    def __init__(
        self,
        consumers: List[Consumer],
        generators: List[BaseGenerator],
        optimizer: BaseOptimizer,
    ) -> None:
        self.consumers = consumers
        self.generators = generators
        self.optimizer = optimizer

    def run(self, hours: int = 24) -> List[OptimizationResult]:
        results: List[OptimizationResult] = []
        for hour in range(hours):
            result = self.optimizer.optimize(hour, self.consumers, self.generators)
            results.append(result)
        return results
