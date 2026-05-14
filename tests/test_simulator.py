import pytest
from src.models import (
    Consumer,
    ConstantGenerator,
    ConstantOutput,
    VariableProfileGenerator,
)
from src.optimizers import GreedyOptimizer
from src.simulator import Simulator


# ==========================================
# ТЕСТЫ ДЛЯ МОДЕЛЕЙ (models.py)
# ==========================================

def test_consumer():
    consumer = Consumer(name="House_1", hourly_consumption=[10.0, 15.0, 20.0])
    assert consumer.name == "House_1"
    assert consumer.get_demand(hour=0) == 10.0
    assert consumer.get_demand(hour=2) == 20.0

def test_constant_generator():
    gen = ConstantGenerator(name="Diesel", cost=5.0, capacity=100.0)
    assert gen.name == "Diesel"
    assert gen.get_generation(hour=10) == 100.0
    assert gen.get_cost(hour=10) == 5.0

def test_constant_output_generator():
    # Мощность постоянная, а цена меняется каждый час
    cost_profile = [2.0, 4.0, 6.0]
    gen = ConstantOutput(name="Nuclear", cost_profile=cost_profile, capacity=500.0)
    assert gen.get_generation(hour=1) == 500.0
    assert gen.get_cost(hour=0) == 2.0
    assert gen.get_cost(hour=2) == 6.0

def test_variable_profile_generator():
    # Мощность и цена меняются каждый час
    gen_profile = [0.0, 50.0, 100.0]
    cost_profile = [1.0, 1.5, 2.0]
    gen = VariableProfileGenerator(
        name="Solar", 
        generation_profile=gen_profile, 
        cost_profile=cost_profile
    )
    assert gen.get_generation(hour=1) == 50.0
    assert gen.get_cost(hour=2) == 2.0


# ==========================================
# ТЕСТЫ ДЛЯ ОПТИМИЗАТОРА (optimizers.py)
# ==========================================

@pytest.fixture
def optimizer():
    return GreedyOptimizer()

def test_optimizer_excess_generation(optimizer):
    """Сценарий: энергии хватает на всех. Должны использовать самые дешевые генераторы."""
    consumers = [
        Consumer("C1", [10.0]*24),
        Consumer("C2", [20.0]*24)
    ] # Общий спрос = 30.0
    
    generators = [
        ConstantGenerator("Cheap_Gen", cost=1.0, capacity=50.0),
        ConstantGenerator("Exp_Gen", cost=10.0, capacity=50.0)
    ]
    
    result = optimizer.optimize(hour=0, consumers=consumers, generators=generators)
    
    assert result.total_demand_satisfied == 30.0
    assert len(result.disconnected_consumers) == 0
    assert "C1" in result.connected_consumers
    assert "C2" in result.connected_consumers
    
    # Проверяем, что жадный алгоритм взял дешевый генератор, а дорогой не тронул
    assert result.generator_schedule["Cheap_Gen"] == 30.0
    assert result.generator_schedule["Exp_Gen"] == 0.0
    assert result.hourly_cost == 30.0 * 1.0

def test_optimizer_deficit_generation(optimizer):
    """Сценарий: дефицит энергии. Должны отключить самых крупных потребителей."""
    consumers = [
        Consumer("Small", [5.0]*24),
        Consumer("Medium", [10.0]*24),
        Consumer("Large", [50.0]*24)
    ] # Общий спрос = 65.0
    
    generators = [
        ConstantGenerator("Gen1", cost=2.0, capacity=20.0) # Емкость всего 20.0
    ]
    
    result = optimizer.optimize(hour=0, consumers=consumers, generators=generators)
    
    # Хватит только на Small (5) и Medium (10). В сумме 15. Large (50) отключается.
    assert result.total_demand_satisfied == 15.0
    assert "Small" in result.connected_consumers
    assert "Medium" in result.connected_consumers
    assert "Large" in result.disconnected_consumers
    
    assert result.generator_schedule["Gen1"] == 15.0
    assert result.hourly_cost == 15.0 * 2.0


def test_optimizer_dynamic_costs(optimizer):
    """Проверка, что алгоритм правильно реагирует на изменение цен в течение дня."""
    consumers = [Consumer("C1", [100.0]*24)]
    
    # G1 дешёвый утром (час 0), G2 дешёвый вечером (час 1)
    g1 = ConstantOutput("G1", cost_profile=[1.0, 10.0], capacity=100.0)
    g2 = ConstantOutput("G2", cost_profile=[10.0, 1.0], capacity=100.0)
    
    # Час 0
    res_hour_0 = optimizer.optimize(0, consumers, [g1, g2])
    assert res_hour_0.generator_schedule["G1"] == 100.0
    assert res_hour_0.generator_schedule["G2"] == 0.0
    
    # Час 1
    res_hour_1 = optimizer.optimize(1, consumers, [g1, g2])
    assert res_hour_1.generator_schedule["G1"] == 0.0
    assert res_hour_1.generator_schedule["G2"] == 100.0


# ==========================================
# ТЕСТЫ ДЛЯ СИМУЛЯТОРА (simulator.py)
# ==========================================

def test_simulator_run():
    consumers = [Consumer("C1", [10.0, 15.0])]
    generators = [ConstantGenerator("G1", cost=5.0, capacity=100.0)]
    
    # Запускаем симулятор на 2 часа
    simulator = Simulator(consumers, generators, GreedyOptimizer())
    results = simulator.run(hours=2)
    
    assert len(results) == 2
    
    # Проверка первого часа
    assert results[0].hour == 0
    assert results[0].total_demand_satisfied == 10.0
    
    # Проверка второго часа
    assert results[1].hour == 1
    assert results[1].total_demand_satisfied == 15.0