from __future__ import annotations
import pandas as pd
import numpy as np

def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()

def daily_range(df: pd.DataFrame) -> pd.Series:
    return (df["h"] - df["l"]).abs()

def drawdown_from_recent_high(close: pd.Series, window: int) -> float:
    recent = close.tail(window)
    if recent.empty:
        return 0.0
    peak = float(recent.max())
    last = float(recent.iloc[-1])
    if peak <= 0:
        return 0.0
    return (peak - last) / peak

def slope(series: pd.Series, window: int = 10) -> float:
    y = series.tail(window).to_numpy(dtype=float)
    if len(y) < max(5, window // 2):
        return 0.0
    x = np.arange(len(y), dtype=float)
    m = np.polyfit(x, y, 1)[0]
    return float(m)
