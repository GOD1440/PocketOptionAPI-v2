"""Machine learning utilities for multi-symbol pattern detection and price prediction."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression


@dataclass
class TickData:
    """Simple structure for tick data."""

    timestamp: float
    price: float
    volume: Optional[float] = None


class MultiSymbolPatternDetector:
    """Basic framework for pattern detection and price prediction."""

    def __init__(self, symbols: List[str], window: int = 100):
        self.symbols = symbols
        self.window = window
        self.buffers: Dict[str, deque] = {symbol: deque(maxlen=window) for symbol in symbols}
        self.models: Dict[str, IsolationForest] = {symbol: IsolationForest(contamination=0.01) for symbol in symbols}
        self.regressors: Dict[str, LinearRegression] = {symbol: LinearRegression() for symbol in symbols}
        self.trained: Dict[str, bool] = {symbol: False for symbol in symbols}

    def add_tick(self, symbol: str, tick: TickData) -> Dict[str, float]:
        """Add tick data and return detection results."""
        if symbol not in self.symbols:
            raise ValueError(f"Unknown symbol {symbol}")
        buffer = self.buffers[symbol]
        buffer.append(tick)
        result = {
            "anomaly_score": 0.0,
            "prediction": tick.price,
        }
        if len(buffer) >= self.window:
            df = pd.DataFrame(buffer)
            X = df[["price"]].values
            if not self.trained[symbol]:
                self.models[symbol].fit(X)
                self.regressors[symbol].fit(np.arange(len(X)).reshape(-1, 1), X)
                self.trained[symbol] = True
            anomaly_score = -self.models[symbol].score_samples(X)[-1]
            next_index = np.array([[len(X)]])
            prediction = float(self.regressors[symbol].predict(next_index)[0])
            result.update({"anomaly_score": float(anomaly_score), "prediction": prediction})
        return result
