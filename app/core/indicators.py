from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, period: int = 20) -> pd.Series:
    return series.rolling(window=period, min_periods=1).mean()


def ema(series: pd.Series, period: int = 20) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def bollinger_bands(series: pd.Series, period: int = 20, std_multiplier: float = 2.0) -> pd.DataFrame:
    sma_series = sma(series, period)
    std_series = series.rolling(window=period, min_periods=1).std()
    upper = sma_series + std_multiplier * std_series
    lower = sma_series - std_multiplier * std_series
    return pd.DataFrame({"upper": upper, "middle": sma_series, "lower": lower})


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    fast = series.ewm(span=fast_period, adjust=False).mean()
    slow = series.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast - slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "histogram": histogram})
