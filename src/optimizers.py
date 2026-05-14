from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from src.models import BaseGenerator, Consumer


@dataclass
class OptimizationResult:
    hour: int
    total_demand_satisfied: float
    hourly_cost: float
    generator_schedule: Dict[str, float]
    connected_consumers: List[str]
    disconnected_consumers: List[str]


class BaseOptimizer(ABC):
    @abstractmethod
    def optimize(
        self,
        hour: int,
        consumers: List[Consumer],
        generators: List[BaseGenerator],
    ) -> OptimizationResult:
        """Returns optimal schedule and disconnected consumers."""


class GreedyOptimizer(BaseOptimizer):
    def optimize(
        self,
        hour: int,
        consumers: List[Consumer],
        generators: List[BaseGenerator],
    ) -> OptimizationResult:
        total_capacity = sum(generator.get_generation(hour) for generator in generators)

        sorted_consumers = sorted(consumers, key=lambda consumer: consumer.get_demand(hour))

        connected: List[str] = []
        disconnected: List[str] = []
        current_demand = 0.0

        for consumer in sorted_consumers:
            demand = consumer.get_demand(hour)
            if current_demand + demand <= total_capacity:
                current_demand += demand
                connected.append(consumer.name)
            else:
                disconnected.append(consumer.name)

        sorted_generators = sorted(generators, key=lambda generator: generator.get_cost(hour))
        generator_schedule: Dict[str, float] = {}
        hourly_cost = 0.0
        demand_left = current_demand

        for generator in sorted_generators:
            capacity = generator.get_generation(hour)
            cost = generator.get_cost(hour)
            if demand_left > 0 and capacity > 0:
                used = min(demand_left, capacity)
                generator_schedule[generator.name] = used
                hourly_cost += used * cost
                demand_left -= used
            else:
                generator_schedule[generator.name] = 0.0

        return OptimizationResult(
            hour=hour,
            total_demand_satisfied=current_demand,
            hourly_cost=hourly_cost,
            generator_schedule=generator_schedule,
            connected_consumers=connected,
            disconnected_consumers=disconnected,
        )
