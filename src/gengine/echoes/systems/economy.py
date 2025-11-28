"""Economy subsystem for Phase 4 (M4.3)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

from ..core import GameState
from ..core.models import District, ResourceStock
from ..settings import EconomySettings


@dataclass(slots=True)
class EconomyReport:
    """Summarizes market prices and ongoing shortages."""

    prices: Dict[str, float]
    shortages: Dict[str, int]

    def to_dict(self) -> Dict[str, Dict[str, float | int]]:
        return {
            "prices": {resource: round(price, 4) for resource, price in self.prices.items()},
            "shortages": self.shortages.copy(),
        }


class EconomySystem:
    """Balances district production/consumption and tracks shortages."""

    def __init__(self, settings: EconomySettings | None = None) -> None:
        self._settings = settings or EconomySettings()
        self._shortage_counters: Dict[str, int] = {}

    def tick(self, state: GameState, *, rng: random.Random) -> EconomyReport:
        prices = dict(state.metadata.get("market_prices", {}))
        for district in state.city.districts:
            self._rebalance_district(district, rng)
        shortages = self._update_shortages(state)
        prices = self._update_prices(prices, shortages)
        state.metadata["market_prices"] = prices
        return EconomyReport(prices=prices, shortages=shortages)

    # ------------------------------------------------------------------
    def _rebalance_district(self, district: District, rng: random.Random) -> None:
        demand_mod = 1.0 + district.modifiers.prosperity * self._settings.demand_prosperity_weight
        for stock in district.resources.values():
            regen_factor = max(
                0.0, self._settings.regen_scale + rng.uniform(-0.05, 0.05)
            )
            production = stock.regen * regen_factor
            consumption = self._resource_demand(stock, district, demand_mod)
            delta = production - consumption
            stock.current = int(_clamp(stock.current + delta, 0, stock.capacity))

    def _resource_demand(self, stock: ResourceStock, district: District, demand_mod: float) -> float:
        population_factor = max(
            district.population / self._settings.demand_population_scale,
            0.3,
        )
        base = self._resource_weight(stock.type)
        unrest_penalty = 1.0 + district.modifiers.unrest * self._settings.demand_unrest_weight
        return base * population_factor * demand_mod * unrest_penalty

    def _resource_weight(self, resource_type: str) -> float:
        return self._settings.base_resource_weights.get(resource_type, 1.5)

    def _update_shortages(self, state: GameState) -> Dict[str, int]:
        active: Dict[str, int] = {}
        for district in state.city.districts:
            for resource, stock in district.resources.items():
                if stock.capacity == 0:
                    continue
                level = stock.current / stock.capacity
                if level <= self._settings.shortage_threshold:
                    counter = self._shortage_counters.get(resource, 0) + 1
                    self._shortage_counters[resource] = counter
                    active[resource] = counter
                else:
                    self._shortage_counters[resource] = 0
        # Only surface shortages that have persisted long enough
        return {
            resource: counter
            for resource, counter in self._shortage_counters.items()
            if counter >= self._settings.shortage_warning_ticks
        }

    def _update_prices(
        self,
        prices: Dict[str, float],
        shortages: Dict[str, int],
    ) -> Dict[str, float]:
        updated: Dict[str, float] = {}
        base_price = max(self._settings.base_price, self._settings.price_floor)
        ceiling = base_price + self._settings.price_max_boost
        for resource, counter in shortages.items():
            target_increase = min(
                counter * self._settings.price_increase_step,
                self._settings.price_max_boost,
            )
            previous = prices.get(resource, base_price)
            target_price = min(ceiling, base_price + target_increase)
            new_price = min(ceiling, max(previous, target_price))
            updated[resource] = round(new_price, 4)
        for resource, price in prices.items():
            if resource not in updated:
                decayed = max(price - self._settings.price_decay, base_price)
                updated[resource] = round(decayed, 4)
        for resource in self._settings.base_resource_weights:
            if resource not in updated:
                updated[resource] = round(base_price, 4)
        return updated


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
