import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import os
from datetime import datetime

class SimpleAnomalyDetector:
    def __init__(self, model_path=None):
        self.isolation_forest = IsolationForest(
            contamination=0.15,  # Increased from 0.1 to detect more anomalies
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1  # Use all CPU cores
        )
        self.scaler = StandardScaler()
        self.feature_columns = [
            'foreign_buy', 'foreign_sell', 'local_buy', 'local_sell',
            'net_foreign', 'net_local', 'buy_sell_ratio', 'foreign_ratio', 'volume_ratio'
        ]
        self.is_trained = False

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def load_model(self, model_path):
        """Load model dari file pickle"""
        try:
            with open(model_path, 'rb') as f:
                loaded_model = pickle.load(f)
            
            # Copy attributes dari model yang diload
            self.isolation_forest = loaded_model.isolation_forest
            self.scaler = loaded_model.scaler
            self.feature_columns = loaded_model.feature_columns
            self.is_trained = loaded_model.is_trained
            
            print(f"✅ Model berhasil dimuat dari {model_path}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.is_trained = False

    def prepare_features(self, df):
        """Prepare features untuk model"""
        required_features = ['foreign_buy', 'foreign_sell', 'local_buy', 'local_sell']
        for col in required_features:
            if col not in df.columns:
                df[col] = 0
        
        # Hitung derived features
        if 'net_foreign' not in df.columns:
            df['net_foreign'] = df['foreign_buy'] - df['foreign_sell']
        if 'net_local' not in df.columns:
            df['net_local'] = df['local_buy'] - df['local_sell']
        if 'buy_sell_ratio' not in df.columns:
            total_buy = df['foreign_buy'] + df['local_buy']
            total_sell = df['foreign_sell'] + df['local_sell']
            df['buy_sell_ratio'] = total_buy / (total_sell + 1)  # Avoid division by zero
        if 'foreign_ratio' not in df.columns:
            total_buy = df['foreign_buy'] + df['local_buy']
            df['foreign_ratio'] = df['foreign_buy'] / (total_buy + 1)  # Avoid division by zero
        
        if 'volume_ratio' not in df.columns:
            df['volume_ratio'] = df['buy_sell_ratio']
        
        X = df[self.feature_columns].copy()

        # Handle missing values dan infinite values
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.bfill().ffill().fillna(0)

        return X

    def train(self, broker_data_list):
        """Train model dengan multiple stocks data"""
        if not broker_data_list:
            print("❌ Tidak ada data training")
            return self

        all_features = []

        for broker_df in broker_data_list:
            X = self.prepare_features(broker_df)
            if not X.empty:
                all_features.append(X)

        if not all_features:
            print("❌ Tidak ada features yang valid untuk training")
            return self

        # Combine all data
        X_combined = pd.concat(all_features, ignore_index=True)

        # Scale features
        X_scaled = self.scaler.fit_transform(X_combined)

        # Train model
        self.isolation_forest.fit(X_scaled)
        self.is_trained = True

        print(f"✅ Model trained dengan {len(X_combined)} samples")
        return self

    def detect_anomalies(self, broker_df):
        """Detect anomalies dalam broker data"""
        if not self.is_trained:
            print("❌ Model belum di-training")
            return broker_df

        X = self.prepare_features(broker_df)
        if X.empty:
            print("❌ Tidak ada features untuk detection")
            return broker_df

        X_scaled = self.scaler.transform(X)

        # Predict anomalies
        predictions = self.isolation_forest.predict(X_scaled)
        anomaly_scores = self.isolation_forest.decision_function(X_scaled)

        # Convert to binary (1 = normal, -1 = anomaly) -> (0 = normal, 1 = anomaly)
        anomalies_binary = [1 if x == -1 else 0 for x in predictions]

        results = broker_df.copy()
        results['ml_anomaly'] = anomalies_binary
        results['anomaly_score'] = anomaly_scores
        results['anomaly_confidence'] = 1 - (1 / (1 + np.exp(-np.abs(anomaly_scores))))

        return results

    def detect_broker_anomalies(self, broker_data):
        """Detect anomalies dan return list of anomaly records"""
        if not self.is_trained:
            print("❌ Model belum di-training")
            return []
        
        try:
            results = self.detect_anomalies(broker_data)
            anomaly_threshold = np.percentile(results['anomaly_score'], 20)  # Bottom 20% are anomalies
            results['ml_anomaly'] = results['anomaly_score'] < anomaly_threshold
            
            anomalies = results[results['ml_anomaly'] == True]
            
            anomaly_records = []
            for _, row in anomalies.iterrows():
                # Hitung severity berdasarkan anomaly score
                score = row.get('anomaly_score', 0)
                confidence = row.get('anomaly_confidence', 0)
                
                severity = 'low'
                if score < np.percentile(results['anomaly_score'], 5):
                    severity = 'critical'
                elif score < np.percentile(results['anomaly_score'], 10):
                    severity = 'high'
                elif score < np.percentile(results['anomaly_score'], 15):
                    severity = 'medium'
                
                anomaly_records.append({
                    'date': row.get('date', datetime.now()).isoformat() if hasattr(row.get('date'), 'isoformat') else str(row.get('date', datetime.now())),
                    'foreign_buy': float(row.get('foreign_buy', 0)),
                    'foreign_sell': float(row.get('foreign_sell', 0)),
                    'local_buy': float(row.get('local_buy', 0)),
                    'local_sell': float(row.get('local_sell', 0)),
                    'net_foreign': float(row.get('net_foreign', 0)),
                    'net_local': float(row.get('net_local', 0)),
                    'volume_ratio': float(row.get('volume_ratio', row.get('buy_sell_ratio', 0))),
                    'anomaly_score': float(row.get('anomaly_score', 0)),
                    'anomaly_confidence': float(row.get('anomaly_confidence', 0)),
                    'severity': severity,
                    'explanation': self._generate_anomaly_explanation(row),
                    'is_anomaly': True  # Added explicit anomaly flag
                })
            
            print(f"✅ Detected {len(anomaly_records)} anomalies out of {len(broker_data)} records")
            return anomaly_records
        except Exception as e:
            print(f"❌ Error dalam deteksi anomali: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _generate_anomaly_explanation(self, row):
        """Generate penjelasan untuk anomali yang terdeteksi"""
        explanations = []
        
        net_foreign = row.get('net_foreign', 0)
        net_local = row.get('net_local', 0)
        buy_sell_ratio = row.get('buy_sell_ratio', 1)
        volume_ratio = row.get('volume_ratio', buy_sell_ratio)
        
        if abs(net_foreign) > 30000:
            if net_foreign > 0:
                explanations.append(f"Asing net buy tinggi: Rp {abs(net_foreign):,.0f}M")
            else:
                explanations.append(f"Asing net sell tinggi: Rp {abs(net_foreign):,.0f}M")
        
        if abs(net_local) > 50000:
            if net_local > 0:
                explanations.append(f"Domestik net buy tinggi: Rp {abs(net_local):,.0f}M")
            else:
                explanations.append(f"Domestik net sell tinggi: Rp {abs(net_local):,.0f}M")
        
        # Check for potential bandar manipulation
        if net_foreign < -30000 and net_local > 50000:
            explanations.append("⚠️ Potensi akumulasi bandar: Asing jual, domestik beli kuat")
        elif net_foreign > 30000 and net_local < -50000:
            explanations.append("⚠️ Potensi distribusi bandar: Asing beli, domestik jual")
        
        if volume_ratio > 1.8:
            explanations.append(f"Tekanan beli berlebihan: {volume_ratio:.2f}x")
        elif volume_ratio < 0.6:
            explanations.append(f"Tekanan jual berlebihan: {volume_ratio:.2f}x")
        
        if not explanations:
            explanations.append("Pola trading tidak normal terdeteksi oleh AI")
        
        return " | ".join(explanations)

    def save_model(self, model_path):
        """Save model ke file pickle"""
        try:
            with open(model_path, 'wb') as f:
                pickle.dump(self, f)
            print(f"✅ Model berhasil disimpan ke {model_path}")
        except Exception as e:
            print(f"❌ Error saving model: {e}")
