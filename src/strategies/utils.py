import pandas as pd

def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=window).mean()

def check_crossover(short_series: pd.Series, long_series: pd.Series) -> str:
    """
    Check for crossover in the last step.
    Returns "GOLDEN" if short crossed above long.
    Returns "DEAD" if short crossed below long.
    Returns "NONE" otherwise.
    """
    if len(short_series) < 2 or len(long_series) < 2:
        return "NONE"
        
    prev_short = short_series.iloc[-2]
    curr_short = short_series.iloc[-1]
    
    prev_long = long_series.iloc[-2]
    curr_long = long_series.iloc[-1]
    
    if prev_short <= prev_long and curr_short > curr_long:
        return "GOLDEN"
    elif prev_short >= prev_long and curr_short < curr_long:
        return "DEAD"
    
    return "NONE"
