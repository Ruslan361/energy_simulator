import argparse
import json
import sys
from typing import List, Tuple

from src.models import (
    BaseGenerator,
    ConstantGenerator,
    ConstantOutput,
    Consumer,
    VariableProfileGenerator,
)
from src.optimizers import GreedyOptimizer
from src.simulator import Simulator


def load_config(config_path: str) -> Tuple[str, List[Consumer], List[BaseGenerator]]:
    """Парсит JSON файл и собирает Python-объекты для симулятора."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл конфигурации '{config_path}' не найден.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Ошибка: Неверный формат JSON в файле '{config_path}': {e}")
        sys.exit(1)

    scenario_name = data.get("scenario_name", "Unknown Scenario")

    # Инициализируем потребителей
    consumers = []
    for c in data.get("consumers", []):
        consumers.append(
            Consumer(name=c["name"], hourly_consumption=c["hourly_consumption"])
        )

    # Инициализируем генераторы в зависимости от их типа
    generators = []
    for g in data.get("generators", []):
        g_type = g.get("type")
        name = g["name"]
        
        if g_type == "ConstantGenerator":
            generators.append(ConstantGenerator(name=name, cost=g["cost"], capacity=g["capacity"]))
        
        elif g_type == "ConstantOutput":
            generators.append(ConstantOutput(name=name, cost_profile=g["cost_profile"], capacity=g["capacity"]))
        
        elif g_type == "VariableProfileGenerator":
            generators.append(
                VariableProfileGenerator(
                    name=name, 
                    generation_profile=g["generation_profile"], 
                    cost_profile=g["cost_profile"]
                )
            )
        else:
            print(f"Предупреждение: Неизвестный тип генератора '{g_type}' пропущен.")

    return scenario_name, consumers, generators


def generate_report_text(scenario_name: str, results: list) -> str:
    """Формирует текстовый отчет по всем 24 часам симуляции."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"ОТЧЕТ О СИМУЛЯЦИИ: {scenario_name}")
    lines.append("=" * 60)

    total_daily_cost = 0.0

    for r in results:
        total_daily_cost += r.hourly_cost
        
        # Вывод результатов КАЖДОГО ЧАСА (как вы просили)
        lines.append(f"\n[Час {r.hour:02d}:00]")
        lines.append(f"  Спрос удовлетворен: {r.total_demand_satisfied:.1f} кВт*ч")
        lines.append(f"  Стоимость генерации: {r.hourly_cost:.2f} у.е.")
        
        active_gens = {k: v for k, v in r.generator_schedule.items() if v > 0}
        lines.append(f"  Работа генераторов: {active_gens}")
        
        if r.disconnected_consumers:
            lines.append(f"  ОТКЛЮЧЕНЫ ({len(r.disconnected_consumers)} шт): {', '.join(r.disconnected_consumers)}")
        else:
            lines.append("  Все потребители запитаны.")

    lines.append("-" * 60)
    lines.append(f"ОБЩАЯ СТОИМОСТЬ ЗА СУТКИ: {total_daily_cost:.2f} у.е.\n")
    
    return "\n".join(lines)


def main():
    # Настройка аргументов командной строки
    parser = argparse.ArgumentParser(description="Energy Grid Simulator CLI")
    parser.add_argument("--config", type=str, required=True, help="Путь к JSON файлу с конфигурацией")
    parser.add_argument("--output", type=str, required=True, help="Путь для сохранения текстового отчета")
    
    args = parser.parse_args()

    print(f"Загрузка конфигурации из {args.config}...")
    scenario_name, consumers, generators = load_config(args.config)
    
    print(f"Запуск симуляции (Сценарий: {scenario_name})...")
    # Инъекция зависимости
    optimizer = GreedyOptimizer()
    simulator = Simulator(consumers, generators, optimizer)
    
    # Запуск
    results = simulator.run(hours=24)
    
    # Генерация текста
    report_text = generate_report_text(scenario_name, results)
    
    # Вывод в консоль
    print(report_text)
    
    # Запись в файл
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"Готово! Подробный отчет успешно сохранен в файл: {args.output}")
    except Exception as e:
        print(f"Ошибка при записи в файл: {e}")


if __name__ == "__main__":
    main()