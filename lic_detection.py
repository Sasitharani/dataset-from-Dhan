import pandas as pd
import numpy as np

def detect_lic(df, volume_multiplier=1.8, **kwargs):
    """
    Detect LIC (Liquidity Imbalance Candle)
    = VOLUME SPIKE (that creates the imbalance)
    
    Parameters:
    - df: DataFrame with OHLCV data
    - volume_multiplier: Volume must be X times average (default 1.8x)
    
    Returns:
    - DataFrame with LIC signals
    """
    
    df = df.copy()
    
    # Calculate average volume (last 20 candles)
    df['avg_volume'] = df['volume'].rolling(window=20, min_periods=1).mean()
    
    # LIC = Volume spike (that's the liquidity imbalance!)
    df['is_lic'] = df['volume'] >= (df['avg_volume'] * volume_multiplier)
    
    # Determine LIC direction (which way volume pushed)
    df['lic_direction'] = 'NONE'
    df.loc[df['is_lic'] & (df['close'] > df['open']), 'lic_direction'] = 'BULL'
    df.loc[df['is_lic'] & (df['close'] < df['open']), 'lic_direction'] = 'BEAR'
    
    return df[['is_lic', 'lic_direction']]

def detect_loc(df, lic_signals, retracement_pct=25, loc_window=6):
    """
    Detect LOC (Liquidity Absorption Candle) after LIC
    
    Parameters:
    - df: DataFrame with OHLCV data
    - lic_signals: DataFrame with LIC signals
    - retracement_pct: LOC must retrace X% of LIC (default 25%)
    - loc_window: Look ahead window for LOC (default 6 candles)
    
    Returns:
    - DataFrame with LOC signals
    """
    
    df = df.copy()
    df['is_loc'] = False
    df['loc_direction'] = 'NONE'
    df['loc_confirmed'] = False
    
    # Find LIC signals
    lic_indices = lic_signals[lic_signals['is_lic']].index
    
    for lic_idx in lic_indices:
        lic_row = df.loc[lic_idx]
        lic_direction = 'BULL' if lic_row['close'] > lic_row['open'] else 'BEAR'
        lic_body = abs(lic_row['close'] - lic_row['open'])
        
        # Look for LOC in next 6 candles
        lic_position = df.index.get_loc(lic_idx)
        search_start = lic_position + 1
        search_end = min(lic_position + loc_window + 1, len(df))
        
        for loc_position in range(search_start, search_end):
            loc_idx = df.index[loc_position]
            loc_row = df.loc[loc_idx]
            loc_direction = 'BULL' if loc_row['close'] > loc_row['open'] else 'BEAR'
            
            # LOC must be opposite direction of LIC
            if lic_direction != loc_direction:
                # Check retracement
                if lic_direction == 'BULL':
                    # LIC went up, LOC should come down and retrace
                    retracement = lic_body * (retracement_pct / 100)
                    if loc_row['low'] <= lic_row['close'] - retracement:
                        df.loc[loc_idx, 'is_loc'] = True
                        df.loc[loc_idx, 'loc_direction'] = loc_direction
                        df.loc[lic_idx, 'loc_confirmed'] = True
                        break
                else:
                    # LIC went down, LOC should come up and retrace
                    retracement = lic_body * (retracement_pct / 100)
                    if loc_row['high'] >= lic_row['close'] + retracement:
                        df.loc[loc_idx, 'is_loc'] = True
                        df.loc[loc_idx, 'loc_direction'] = loc_direction
                        df.loc[lic_idx, 'loc_confirmed'] = True
                        break
    
    return df[['is_loc', 'loc_direction', 'loc_confirmed']]


def identify_patterns(df, lic_signals, loc_signals):
    """
    Combine LIC + LOC to identify complete patterns
    
    Returns:
    - DataFrame with pattern signals (BUY/SELL)
    """
    
    df = df.copy()
    df['signal'] = 'NONE'
    df['signal_type'] = 'NONE'
    
    # Find confirmed LOCs (which means LIC was confirmed)
    confirmed_locs = loc_signals[loc_signals['is_loc']].index
    
    for loc_idx in confirmed_locs:
        # Determine signal direction (opposite of LOC)
        loc_direction = loc_signals.loc[loc_idx, 'loc_direction']
        
        if loc_direction == 'BEAR':
            # LOC is bearish, so reversal expected = BUY
            df.loc[loc_idx, 'signal'] = 'BUY'
            df.loc[loc_idx, 'signal_type'] = 'LIC-LOC Pattern'
        elif loc_direction == 'BULL':
            # LOC is bullish, so reversal expected = SELL
            df.loc[loc_idx, 'signal'] = 'SELL'
            df.loc[loc_idx, 'signal_type'] = 'LIC-LOC Pattern'
    
    return df[['signal', 'signal_type']]
def calculate_pnl(df, signals_df):
    """
    Calculate P&L for each buy/sell pair
    """
    df = df.copy()
    df['pnl'] = None
    df['pnl_pct'] = None
    
    buy_signals = signals_df[signals_df['signal'] == 'BUY'].index.tolist()
    sell_signals = signals_df[signals_df['signal'] == 'SELL'].index.tolist()
    
    for i, buy_idx in enumerate(buy_signals):
        # Find next sell after this buy
        next_sells = [s for s in sell_signals if df.index.get_loc(s) > df.index.get_loc(buy_idx)]
        
        if next_sells:
            sell_idx = next_sells[0]
            entry_price = df.loc[buy_idx, 'close']
            exit_price = df.loc[sell_idx, 'close']
            
            pnl = exit_price - entry_price
            pnl_pct = (pnl / entry_price) * 100
            
            df.loc[buy_idx, 'pnl'] = pnl
            df.loc[buy_idx, 'pnl_pct'] = pnl_pct
            df.loc[sell_idx, 'pnl'] = pnl
            df.loc[sell_idx, 'pnl_pct'] = pnl_pct
    
    return df