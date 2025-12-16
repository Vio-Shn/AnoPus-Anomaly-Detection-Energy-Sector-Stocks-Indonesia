# train_model.py
import yfinance as yf
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Definisikan class yang sama
class SimpleAnomalyDetector:
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.feature_columns = [
            'foreign_buy', 'foreign_sell', 'local_buy', 'local_sell',
            'net_foreign', 'net_local', 'buy_sell_ratio', 'foreign_ratio'
        ]
        self.is_trained = False

    def prepare_features(self, df):
        available_columns = [col for col in self.feature_columns if col in df.columns]
        if not available_columns:
            return pd.DataFrame()
        X = df[available_columns].copy()
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.bfill().ffill().fillna(0)
        return X

    def train(self, broker_data_list):
        if not broker_data_list:
            return self
        all_features = []
        for broker_df in broker_data_list:
            X = self.prepare_features(broker_df)
            if not X.empty:
                all_features.append(X)
        if not all_features:
            return self
        X_combined = pd.concat(all_features, ignore_index=True)
        X_scaled = self.scaler.fit_transform(X_combined)
        self.isolation_forest.fit(X_scaled)
        self.is_trained = True
        print(f"✅ Model trained dengan {len(X_combined)} samples")
        return self

    def detect_anomalies(self, broker_df):
        if not self.is_trained:
            return broker_df
        X = self.prepare_features(broker_df)
        if X.empty:
            return broker_df
        X_scaled = self.scaler.transform(X)
        predictions = self.isolation_forest.predict(X_scaled)
        anomaly_scores = self.isolation_forest.decision_function(X_scaled)
        anomalies_binary = [1 if x == -1 else 0 for x in predictions]
        results = broker_df.copy()
        results['ml_anomaly'] = anomalies_binary
        results['anomaly_score'] = anomaly_scores
        results['anomaly_confidence'] = 1 - (1 / (1 + np.exp(-np.abs(anomaly_scores))))
        return results

def generate_sample_broker_data():
    """Generate sample data untuk training"""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    broker_data = []
    
    for date in dates:
        # Data normal
        foreign_buy = max(1000, abs(np.random.normal(50000, 20000)))
        foreign_sell = max(1000, abs(np.random.normal(45000, 18000)))
        local_buy = max(1000, abs(np.random.normal(80000, 30000)))
        local_sell = max(1000, abs(np.random.normal(75000, 28000)))
        
        # Beberapa anomali
        if np.random.random() < 0.05:  # 5% anomali
            if np.random.random() < 0.5:
                # Distribution pattern
                foreign_sell *= np.random.uniform(3, 6)
                local_sell *= np.random.uniform(2, 4)
            else:
                # Accumulation pattern  
                foreign_buy *= np.random.uniform(3, 5)
                local_buy *= np.random.uniform(2, 3)
        
        net_foreign = foreign_buy - foreign_sell
        net_local = local_buy - local_sell
        total_volume = foreign_buy + foreign_sell + local_buy + local_sell
        buy_sell_ratio = (foreign_buy + local_buy) / max(1, (foreign_sell + local_sell))
        foreign_ratio = foreign_buy / max(1, (foreign_buy + foreign_sell))
        
        record = {
            'date': date,
            'stock_code': 'SAMPLE',
            'foreign_buy': foreign_buy,
            'foreign_sell': foreign_sell,
            'local_buy': local_buy,
            'local_sell': local_sell,
            'net_foreign': net_foreign,
            'net_local': net_local,
            'total_volume': total_volume,
            'buy_sell_ratio': buy_sell_ratio,
            'foreign_ratio': foreign_ratio
        }
        broker_data.append(record)
    
    return pd.DataFrame(broker_data)

def train_and_save_model():
    """Train model dan simpan"""
    print("🚀 Training anomaly detection model...")
    
    # Buat sample data untuk training
    sample_data = generate_sample_broker_data()
    
    # Train model
    detector = SimpleAnomalyDetector()
    detector.train([sample_data])
    
    # Simpan model
    os.makedirs('energy_stocks_data', exist_ok=True)
    model_path = 'energy_stocks_data/anomaly_detector.pkl'
    
    with open(model_path, 'wb') as f:
        pickle.dump(detector, f)
    
    print(f"✅ Model saved to: {model_path}")
    return detector

if __name__ == "__main__":
    train_and_save_model()