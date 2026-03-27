from __future__ import annotations

from scripts.strategies import building_steel, cold_rolling, hot_rolling, stainless_flat

STRATEGIES = {
    cold_rolling.STRATEGY_NAME: cold_rolling,
    hot_rolling.STRATEGY_NAME: hot_rolling,
    building_steel.STRATEGY_NAME: building_steel,
    stainless_flat.STRATEGY_NAME: stainless_flat,
}
