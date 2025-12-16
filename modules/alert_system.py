from datetime import datetime

class AlertSystem:
    """Sistem untuk generate alerts berdasarkan technical signals dan anomalies"""
    
    @staticmethod
    def generate_alerts(technical_analysis, anomalies=None, stock_data=None):
        """Generate alerts dari technical analysis dan anomalies"""
        alerts = []
        
        timestamp = datetime.now()
        
        # Alert dari technical signals
        if technical_analysis.get('rsi_signal') == 'OVERBOUGHT':
            alerts.append({
                'type': 'HIGH',
                'severity': 'HIGH',
                'title': 'RSI_OVERBOUGHT',
                'message': 'RSI menunjukkan kondisi overbought (>70)',
                'action': 'SELL',
                'timestamp': timestamp
            })
        
        if technical_analysis.get('rsi_signal') == 'OVERSOLD':
            alerts.append({
                'type': 'HIGH',
                'severity': 'HIGH',
                'title': 'RSI_OVERSOLD',
                'message': 'RSI menunjukkan kondisi oversold (<30)',
                'action': 'BUY',
                'timestamp': timestamp
            })
        
        if technical_analysis.get('ma_signal') == 'BULLISH':
            alerts.append({
                'type': 'MA_BULLISH',
                'severity': 'LOW',
                'message': 'Moving Average menunjukkan trend bullish',
                'action': 'BUY',
                'timestamp': timestamp
            })
        
        if technical_analysis.get('ma_signal') == 'BEARISH':
            alerts.append({
                'type': 'MA_BEARISH',
                'severity': 'MEDIUM',
                'message': 'Moving Average menunjukkan trend bearish',
                'action': 'SELL',
                'timestamp': timestamp
            })
        
        if technical_analysis.get('volume_signal') == 'HIGH':
            alerts.append({
                'type': 'VOLUME_HIGH',
                'severity': 'MEDIUM',
                'message': 'Volume trading lebih tinggi dari rata-rata',
                'action': 'MONITOR',
                'timestamp': timestamp
            })
        
        # Alert dari anomalies
        if anomalies:
            for anomaly in anomalies:
                if anomaly.get('anomaly_confidence', 0) > 0.8:
                    alerts.append({
                        'type': 'ANOMALY_DETECTED',
                        'severity': 'HIGH',
                        'message': f"Anomali terdeteksi dengan confidence {anomaly.get('anomaly_confidence', 0):.2%}",
                        'action': 'INVESTIGATE',
                        'timestamp': timestamp
                    })
        
        return alerts
    
    @staticmethod
    def get_daily_alerts():
        """Get daily alerts (placeholder untuk future implementation)"""
        return []
