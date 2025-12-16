"""Script untuk training anomaly detector model"""
import os
import sys
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.anomaly_detector import SimpleAnomalyDetector
from modules.data_collector import DataCollector

def train_and_save_model():
    """Train model dengan data dari berbagai stocks"""
    print("=" * 60)
    print("🚀 Starting Anomaly Detector Model Training")
    print("=" * 60)
    
    # Initialize detector
    detector = SimpleAnomalyDetector()
    
    # Collect training data dari beberapa stocks
    collector = DataCollector()
    energy_stocks = ['ADRO.JK', 'PTBA.JK', 'BYAN.JK', 'ITMG.JK', 'GEMS.JK']
    
    all_broker_data = []
    
    print("\n📊 Collecting training data from multiple stocks...")
    for stock in energy_stocks:
        print(f"  → Collecting data for {stock}...", end=" ")
        try:
            broker_data = collector.get_broker_summary(stock, '6mo')
            if not broker_data.empty:
                all_broker_data.append(broker_data)
                print(f"✓ ({len(broker_data)} records)")
            else:
                print("⚠️ No data")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    if not all_broker_data:
        print("\n❌ No training data collected!")
        return False
    
    print(f"\n✅ Total {len(all_broker_data)} datasets collected")
    
    # Train model
    print("\n🤖 Training model with Isolation Forest...")
    try:
        detector.train(all_broker_data)
        print("✅ Model training completed successfully!")
    except Exception as e:
        print(f"❌ Error during training: {e}")
        return False
    
    # Save model
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'anomaly_detector.pkl')
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    print(f"\n💾 Saving model to {model_path}...")
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(detector, f)
        print("✅ Model saved successfully!")
        return True
    except Exception as e:
        print(f"❌ Error saving model: {e}")
        return False

if __name__ == '__main__':
    success = train_and_save_model()
    print("\n" + "=" * 60)
    if success:
        print("✨ Training process completed successfully!")
    else:
        print("⚠️ Training process failed. Please try again.")
    print("=" * 60)
