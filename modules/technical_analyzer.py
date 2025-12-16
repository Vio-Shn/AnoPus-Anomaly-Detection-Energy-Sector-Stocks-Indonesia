# modules/technical_analyzer.py
import pandas as pd
import numpy as np

class TechnicalAnalyzer:
    def __init__(self):
        self.rsi_period = 14
        self.ma_short = 5
        self.ma_long = 20

    def calculate_rsi(self, prices, period=14):
        """Menghitung Relative Strength Index (RSI)"""
        if len(prices) < period:
            return pd.Series([np.nan] * len(prices), index=prices.index)

        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_moving_averages(self, prices, short_window=5, long_window=20):
        """Menghitung Simple Moving Average (MA) pendek dan panjang"""
        ma_short = prices.rolling(window=short_window, min_periods=1).mean()
        ma_long = prices.rolling(window=long_window, min_periods=1).mean()
        return ma_short, ma_long

    def analyze(self, stock_data):
        """Analisis teknikal lengkap untuk data saham"""
        if stock_data.empty or 'Close' not in stock_data.columns:
            return {
                'rsi': 50,
                'rsi_signal': 'NEUTRAL',
                'ma_signal': 'NEUTRAL',
                'current_price': 0,
                'price_change': 0
            }
        
        closes = stock_data['Close'].astype(float)
        rsi = self.calculate_rsi(closes, self.rsi_period)
        ma_short, ma_long = self.calculate_moving_averages(closes, self.ma_short, self.ma_long)
        
        last_rsi = rsi.iloc[-1] if not rsi.empty else 50
        last_ma_short = ma_short.iloc[-1] if not ma_short.empty else 0
        last_ma_long = ma_long.iloc[-1] if not ma_long.empty else 0
        current_price = closes.iloc[-1] if not closes.empty else 0
        
        # Hitung persentase perubahan harga
        price_change = ((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100) if len(closes) > 1 else 0
        
        # Tentukan sinyal RSI
        if last_rsi > 70:
            rsi_signal = "OVERBOUGHT"
        elif last_rsi < 30:
            rsi_signal = "OVERSOLD"
        else:
            rsi_signal = "NEUTRAL"
        
        # Tentukan sinyal MA
        if last_ma_short > last_ma_long:
            ma_signal = "BULLISH"
        elif last_ma_short < last_ma_long:
            ma_signal = "BEARISH"
        else:
            ma_signal = "NEUTRAL"
        
        return {
            'rsi': round(float(last_rsi), 2),
            'rsi_signal': rsi_signal,
            'ma_signal': ma_signal,
            'current_price': round(float(current_price), 2),
            'price_change': round(float(price_change), 2)
        }
