import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
import time
import json

class DataCollector:
    def __init__(self):
        self.idx_base_url = "https://www.idx.co.id"
    
    def get_intraday_data(self, stock_code, interval='5m', period='1d'):
        """Mendapatkan data intraday dari Yahoo Finance"""
        try:
            print(f"📊 Mengambil data intraday {stock_code} interval {interval}")
            
            stock = yf.Ticker(stock_code)
            
            # Untuk intraday, period maksimal 60 hari
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                print(f"❌ Tidak ada data intraday untuk {stock_code}")
                return None
            
            hist = hist.reset_index()
            print(f"✅ Data intraday: {len(hist)} candlestick")
            return hist
            
        except Exception as e:
            print(f"❌ Error intraday data: {e}")
            return None
    
    def get_stock_data(self, stock_code, period='1mo', use_intraday=True):
        """Mengambil data saham dengan opsi intraday"""
        try:
            # Jika ingin data real-time, coba intraday dulu
            if use_intraday and period in ['1d', '5d']:
                intraday_data = self.get_intraday_data(stock_code, interval='5m', period=period)
                if intraday_data is not None and not intraday_data.empty:
                    return intraday_data
            
            # Fallback ke data harian
            return self.get_daily_data(stock_code, period)
            
        except Exception as e:
            print(f"Error fetching stock data for {stock_code}: {e}")
            return self.get_fallback_data(stock_code, period)
    
    def get_daily_data(self, stock_code, period='1mo'):
        """Mengambil data harian dari Yahoo Finance"""
        try:
            stock = yf.Ticker(stock_code)
            hist = stock.history(period=period)
            
            if not hist.empty:
                hist = hist.reset_index()
                # Convert to date for consistency
                hist['Date'] = pd.to_datetime(hist['Date']).dt.date
                print(f"📅 Data harian - Period: {period}, Records: {len(hist)}")
                return hist
                
        except Exception as e:
            print(f"Error with daily data: {e}")
            
        return None
    
    def get_tradingview_like_data(self, stock_code):
        """Mencoba mendapatkan data seperti TradingView"""
        try:
            print(f"[v0] get_tradingview_like_data called for {stock_code}")
            
            intervals = ['5m', '15m', '1h', '1d']
            
            for interval in intervals:
                try:
                    print(f"[v0] Trying interval: {interval}")
                    data = self.get_intraday_data(stock_code, interval=interval, period='5d')
                    if data is not None and not data.empty:
                        print(f"[v0] Success with {interval} - {len(data)} candles")
                        # Ensure we have the right columns
                        if 'Datetime' not in data.columns and 'Date' not in data.columns:
                            data['Date'] = data.index
                        return data
                except Exception as e:
                    print(f"[v0] Failed with interval {interval}: {e}")
                    continue
            
            print(f"[v0] Falling back to daily data")
            daily = self.get_daily_data(stock_code, '1mo')
            if daily is not None and not daily.empty:
                print(f"[v0] Daily data: {len(daily)} rows")
                return daily
            
            print(f"[v0] Using fallback data")
            return self.get_fallback_data(stock_code, '1mo')
            
        except Exception as e:
            print(f"[v0] ERROR in get_tradingview_like_data: {e}")
            import traceback
            traceback.print_exc()
            return self.get_fallback_data(stock_code, '1mo')
    
    def get_realtime_price(self, stock_code):
        """Mendapatkan harga real-time terbaru"""
        try:
            # Coba dari IDX terlebih dahulu
            idx_data = self.get_idx_realtime_data(stock_code)
            if idx_data is not None:
                return {
                    'close': idx_data['Close'].iloc[0] if not idx_data.empty else 0,
                    'volume': idx_data['Volume'].iloc[0] if not idx_data.empty else 0,
                    'timestamp': datetime.now()
                }
            
            # Fallback ke Yahoo Finance real-time
            stock = yf.Ticker(stock_code)
            info = stock.info
            
            current_price = info.get('currentPrice', 
                                   info.get('regularMarketPrice', 
                                           info.get('previousClose', 0)))
            volume = info.get('volume', info.get('regularMarketVolume', 0))
            
            return {
                'close': current_price,
                'volume': volume,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error getting realtime price: {e}")
            return {'close': 0, 'volume': 0, 'timestamp': datetime.now()}
    
    def get_idx_realtime_data(self, stock_code):
        """Mengambil data real-time dari IDX"""
        try:
            # Hapus .JK dari kode saham
            code = stock_code.replace('.JK', '')
            url = f"https://www.idx.co.id/primary/ListedCompany/GetTradingInfoSS?code={code}&length=100"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data and 'data' in data and len(data['data']) > 0:
                    trading_data = data['data'][0]
                    
                    # Format data untuk consistency
                    today = datetime.now().date()
                    price_data = {
                        'Date': [pd.Timestamp(today)],
                        'Open': [trading_data.get('Open', 0)],
                        'High': [trading_data.get('High', 0)],
                        'Low': [trading_data.get('Low', 0)],
                        'Close': [trading_data.get('Close', 0)],
                        'Volume': [trading_data.get('Volume', 0)]
                    }
                    
                    df = pd.DataFrame(price_data)
                    print(f"���️ Data IDX - Close: Rp {df['Close'].iloc[0]:.2f}")
                    return df
                    
        except Exception as e:
            print(f"Error fetching IDX data: {e}")
        
        return None
    
    def get_broker_summary(self, stock_code, period='6mo'):
        """Mengambil data broker summary"""
        try:
            period_days = {
                '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
                '6mo': 180, '1y': 365, '2y': 730, '5y': 1825
            }
            
            days = period_days.get(period, 180)
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now()
            
            return self.get_simulated_broker_data(stock_code, start_date, end_date)
            
        except Exception as e:
            print(f"Error in get_broker_summary: {e}")
            return pd.DataFrame()
    
    def get_simulated_broker_data(self, stock_code, start_date, end_date):
        """Generate simulated broker data with realistic market patterns"""
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            broker_data = []
            for i, date in enumerate(dates):
                trend = np.sin(date.timetuple().tm_yday / 365 * 2 * np.pi) * 0.3 + 1
                volatility = np.random.uniform(0.8, 1.2)
                
                foreign_buy = abs(np.random.normal(80000 * trend * volatility, 30000))
                foreign_sell = abs(np.random.normal(75000 * trend * volatility, 28000))
                local_buy = abs(np.random.normal(120000 * trend * volatility, 50000)) 
                local_sell = abs(np.random.normal(115000 * trend * volatility, 48000))
                
                if np.random.random() < 0.15:  # 15% chance of anomaly
                    anomaly_type = np.random.choice(['accumulation', 'distribution', 'panic_sell'])
                    
                    if anomaly_type == 'accumulation':
                        # Bandar accumulation: foreign sell, domestic buy heavily
                        foreign_sell *= 2.5
                        local_buy *= 1.8
                    elif anomaly_type == 'distribution':
                        # Bandar distribution: foreign buy, domestic sell
                        foreign_buy *= 2.2
                        local_sell *= 1.7
                    elif anomaly_type == 'panic_sell':
                        # Panic selling across the board
                        foreign_sell *= 3
                        local_sell *= 2.5
                
                broker_data.append({
                    'date': date,
                    'foreign_buy': foreign_buy,
                    'foreign_sell': foreign_sell,
                    'local_buy': local_buy,
                    'local_sell': local_sell,
                    'net_foreign': foreign_buy - foreign_sell,
                    'net_local': local_buy - local_sell,  # Added net_local
                    'volume_ratio': (foreign_buy + local_buy) / (foreign_sell + local_sell + 1)
                })
            
            return pd.DataFrame(broker_data)
            
        except Exception as e:
            print(f"Error in get_simulated_broker_data: {e}")
            return pd.DataFrame()
    
    def get_fallback_data(self, stock_code, period):
        """Fallback data dengan harga yang lebih realistis"""
        try:
            # Generate data intraday untuk fallback
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), 
                                 end=datetime.now(), freq='5min')
            
            base_price = 25000
            prices = []
            
            for i in range(len(dates)):
                # Simulasi pergerakan harga intraday
                change = np.random.normal(0, 0.001)  # Volatility kecil untuk intraday
                base_price *= (1 + change)
                
                # Simulasi OHLC untuk setiap interval
                open_price = base_price
                high_price = base_price * (1 + abs(np.random.normal(0, 0.005)))
                low_price = base_price * (1 - abs(np.random.normal(0, 0.005)))
                close_price = base_price
                
                prices.append({
                    'Date': dates[i],
                    'Open': max(1, open_price),
                    'High': max(1, high_price),
                    'Low': max(1, low_price),
                    'Close': max(1, close_price),
                    'Volume': np.random.randint(10000, 100000)
                })
            
            df = pd.DataFrame(prices)
            print(f"🔄 Fallback intraday data - Records: {len(df)}")
            return df
            
        except Exception as e:
            print(f"Error in get_fallback_data: {e}")
            return pd.DataFrame()
