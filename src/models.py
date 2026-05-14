from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class Consumer:
    name: str
    hourly_consumption: List[float]

    def get_demand(self, hour: int) -> float:
        return self.hourly_consumption[hour]


class BaseGenerator(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def get_generation(self, hour: int) -> float:
        """Возвращает доступное к генерации количество энергии."""

    @abstractmethod
    def get_cost(self, hour: int) -> float:
        """Возвращает стоимость 1 единицы энергии."""


class ConstantGenerator(BaseGenerator):
    def __init__(self, name: str, cost: float, capacity: float) -> None:
        super().__init__(name)
        self.capacity = capacity
        self.cost = cost

    def get_generation(self, hour: int) -> float:
        return self.capacity

    def get_cost(self, hour: int) -> float:
        return self.cost


class ConstantOutput(BaseGenerator):
    def __init__(
            self, 
            name: str, 
            cost_profile: List[float], 
            capacity: float) -> None:
        super().__init__(name)
        self.capacity = capacity
        self.cost_profile = cost_profile

    def get_generation(self, hour: int) -> float:
        return self.capacity

    def get_cost(self, hour: int) -> float:
        return self.cost_profile[hour]


class VariableProfileGenerator(BaseGenerator):
    def __init__(
        self,
        name: str,
        generation_profile: List[float],
        cost_profile: List[float],
    ) -> None:
        super().__init__(name)
        self.generation_profile = generation_profile
        self.cost_profile = cost_profile

    def get_generation(self, hour: int) -> float:
        return self.generation_profile[hour]

    def get_cost(self, hour: int) -> float:
        if self.cost_profile:
            return self.cost_profile[hour]