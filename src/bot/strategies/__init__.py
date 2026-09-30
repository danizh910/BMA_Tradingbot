"""Strategien S1–S4, Benchmark und Ensemble.

STRATEGIES: die vier Einzelstrategien in fester Reihenfolge (S1–S4).
"""

from bot.strategies.feargreed_trend import FearGreedTrend
from bot.strategies.momentum_atr import MomentumAtr
from bot.strategies.rsi_reversion import RsiReversion
from bot.strategies.sma_crossover import SmaCrossover

STRATEGIES = [SmaCrossover, MomentumAtr, RsiReversion, FearGreedTrend]
