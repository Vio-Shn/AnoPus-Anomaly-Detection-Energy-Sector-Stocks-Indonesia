from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import time
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone
import pandas as pd
import os
import pickle
import yfinance as yf
import numpy as np
from modules.data_collector import DataCollector
from modules.anomaly_detector import SimpleAnomalyDetector
from modules.technical_analyzer import TechnicalAnalyzer
from modules.alert_system import AlertSystem
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'anopus-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anopus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/profiles'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'anomaly_detector.pkl')
anomaly_detector = None
model_trained_once = False

data_collector = None

def init_anomaly_detector():
    """Initialize anomaly detector dengan model yang sudah ada"""
    global anomaly_detector
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                anomaly_detector = pickle.load(f)
            print("✅ Model anomaly detector berhasil di-load dari pickle")
        else:
            print(f"⚠️ Model file tidak ditemukan di {MODEL_PATH}, membuat instance baru")
            anomaly_detector = SimpleAnomalyDetector()
    except Exception as e:
        print(f"❌ Error initializing anomaly detector: {e}")
        anomaly_detector = SimpleAnomalyDetector()

def auto_train_model():
    """Auto-train model if not trained (run only once)"""
    global anomaly_detector, model_trained_once
    
    if model_trained_once or (anomaly_detector and anomaly_detector.is_trained):
        return
    
    try:
        print("⏳ Auto-training anomaly detector model...")
        energy_stocks = ['ADRO.JK', 'PTBA.JK', 'BYAN.JK', 'ITMG.JK', 'GEMS.JK']
        training_data = []
        
        for stock in energy_stocks:
            broker_data = data_collector.get_broker_summary(stock, '6mo')
            if not broker_data.empty:
                training_data.append(broker_data)
        
        if training_data and anomaly_detector:
            anomaly_detector.train(training_data)
            print("✅ Anomaly detector model trained successfully")
            model_trained_once = True
    except Exception as e:
        print(f"⚠️ Error auto-training model: {e}")

def init_data_collector():
    """Initialize data collector"""
    global data_collector
    try:
        data_collector = DataCollector()
        print("✅ DataCollector berhasil diinisialisasi")
    except Exception as e:
        print(f"❌ Error initializing DataCollector: {e}")
        data_collector = None

@app.before_request
def before_request():
    """Initialize modules sebelum request diproses"""
    global data_collector, anomaly_detector, model_trained_once
    
    # Initialize data collector jika belum
    if data_collector is None:
        init_data_collector()
    
    # Initialize anomaly detector jika belum
    if anomaly_detector is None:
        init_anomaly_detector()

# Model User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    # phone = db.Column(db.String(20), nullable=True)
    # profile_photo = db.Column(db.String(200), nullable=True, default='default-avatar.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    watchlists = db.relationship('Watchlist', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def phone(self):
        return getattr(self, '_phone', None)
    
    @property
    def profile_photo(self):
        return getattr(self, '_profile_photo', 'default-avatar.png')

# Model Watchlist
class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_code = db.Column(db.String(20), nullable=False)
    stock_name = db.Column(db.String(100), nullable=False)
    added_date = db.Column(db.DateTime, default=lambda: datetime.now(pytz_timezone('Asia/Jakarta')))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'stock_code', name='unique_user_stock'),)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Daftar saham energi dengan nama lengkap
ENERGY_STOCKS = {
    'ADRO.JK': 'Adaro Energy Indonesia Tbk',
    'PTBA.JK': 'Bukit Asam Tbk',
    'BYAN.JK': 'Bayan Resources Tbk',
    'ITMG.JK': 'Indo Tambangraya Megah Tbk',
    'GEMS.JK': 'Golden Energy Mines Tbk',
    'MCOL.JK': 'Prima Andalan Mandiri Tbk',
    'SMMT.JK': 'Golden Eagle Energy Tbk',
    'RMKE.JK': 'RMK Energy Tbk',
    'KKGI.JK': 'Resource Alam Indonesia Tbk',
    'TOBA.JK': 'TBS Energi Utama Tbk',
    'ARII.JK': 'Atlas Resources Tbk',
    'DEWA.JK': 'Darma Henwa Tbk',
    'MYOH.JK': 'Samindo Resources Tbk',
    'TEBE.JK': 'Dana Brata Luhur Tbk',
    'DOID.JK': 'Delta Dunia Makmur Tbk',
    'RATU.JK': 'Mustika Ratu Tbk',
    'MEDC.JK': 'Medco Energi Internasional Tbk',
    'PGAS.JK': 'Perusahaan Gas Negara Tbk',
    'ENRG.JK': 'Energi Mega Persada Tbk',
    'INDY.JK': 'Indika Energy Tbk',
    'RAJA.JK': 'Rukun Raharja Tbk',
    'ESSA.JK': 'Surya Esa Perkasa Tbk',
    'BIPI.JK': 'Astrindo Nusantara Infrastruktur Tbk',
    'PGEO.JK': 'Pertamina Geothermal Energy Tbk',
    'BREN.JK': 'Barito Renewables Energy Tbk',
    'OASA.JK': 'Maharaksa Biru Energi Tbk',
    'SEMA.JK': 'Semacom Integrated Tbk',
    'JSKY.JK': 'Sky Energy Indonesia Tbk',
    'BRPT.JK': 'Barito Pacific Tbk',
    'CUAN.JK': 'Petrindo Jaya Kreasi Tbk',
    'CDIA.JK': 'Chandra Daya Investasi Tbk',
    'AKRA.JK': 'AKR Corporindo Tbk',
    'PTRO.JK': 'Petrosea Tbk',
    'MBAP.JK': 'Mitrabara Adiperdana Tbk',
    'BUMI.JK': 'Bumi Resources Tbk'
}

@app.route('/')
def landing():
    """Landing page untuk pengunjung belum login"""
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validasi
        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan!', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!', 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Login berhasil! Selamat datang {username}.', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('landing'))

def get_stock_data_real_time(stock_code, period='1mo'):
    """Mendapatkan data saham real-time dengan update candlestick terakhir"""
    try:
        print(f"🔄 Mengambil data real-time untuk {stock_code} periode {period}")
        
        realtime_info = data_collector.get_realtime_price(stock_code)
        current_price = realtime_info['close']
        current_volume = realtime_info['volume']
        
        stock_data = data_collector.get_stock_data(stock_code, period)
        
        if stock_data is None or stock_data.empty:
            print(f"❌ Tidak ada data historis untuk {stock_code}")
            return {
                'stock_code': stock_code,
                'current_price': 0,
                'price_change': 0,
                'price_change_pct': 0,
                'volume': 0,
                'stock_data': [],
                'success': False,
                'stock_name': ENERGY_STOCKS.get(stock_code, stock_code),
                'error': f'Tidak ada data untuk {stock_code}'
            }
        
        if not stock_data.empty and current_price > 0:
            today = datetime.now().date()
            last_date = stock_data['Date'].iloc[-1].date() if hasattr(stock_data['Date'].iloc[-1], 'date') else stock_data['Date'].iloc[-1]
            
            if last_date == today:
                stock_data.loc[stock_data.index[-1], 'Close'] = current_price
                stock_data.loc[stock_data.index[-1], 'High'] = max(stock_data['High'].iloc[-1], current_price)
                stock_data.loc[stock_data.index[-1], 'Low'] = min(stock_data['Low'].iloc[-1], current_price)
                stock_data.loc[stock_data.index[-1], 'Volume'] = current_volume
            else:
                today_data = {
                    'Date': pd.Timestamp(today),
                    'Open': current_price,
                    'High': current_price,
                    'Low': current_price,
                    'Close': current_price,
                    'Volume': current_volume
                }
                stock_data = pd.concat([stock_data, pd.DataFrame([today_data])], ignore_index=True)
        
        chart_data = []
        for index, row in stock_data.iterrows():
            date_str = row['Date'].strftime('%Y-%m-%d') if hasattr(row['Date'], 'strftime') else str(row['Date'])
            chart_data.append({
                'time': date_str,
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row.get('Volume', 0))
            })
        
        if len(chart_data) > 1:
            previous_close = chart_data[-2]['close']
            price_change = ((current_price - previous_close) / previous_close) * 100
        else:
            price_change = 0
        
        latest_data = stock_data.iloc[-1] if len(stock_data) > 0 else None
        
        stock_name = ENERGY_STOCKS.get(stock_code, stock_code)
        price_change_pct = price_change
        
        return {
            'stock_code': stock_code,
            'current_price': current_price,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volume': current_volume,
            'stock_data': chart_data,
            'success': True,
            'stock_name': stock_name
        }
    
    except Exception as e:
        print(f"❌ Error getting stock data for {stock_code}: {e}")
        return {
            'stock_code': stock_code,
            'current_price': 0,
            'price_change': 0,
            'price_change_pct': 0,
            'volume': 0,
            'stock_data': [],
            'success': False,
            'stock_name': stock_code,
            'error': str(e)
        }

def get_technical_signals_real_time(stock_data):
    """Menghitung sinyal teknis dari data saham real-time"""
    if not stock_data or (not stock_data.get('success', False) and not stock_data.get('stock_data')):
        return {
            'rsi': 0,
            'rsi_signal': 'N/A',
            'ma_signal': 'N/A',
            'macd_signal': 'N/A',
            'volume_signal': 'N/A',
            'volume_description': 'Tidak tersedia',
            'avg_volume': 0,
            'current_price': stock_data.get('current_price', 0) if stock_data else 0,
            'price_change': stock_data.get('price_change', 0) if stock_data else 0,
            'price_change_pct': stock_data.get('price_change_pct', 0) if stock_data else 0,
            'volume': stock_data.get('volume', 0) if stock_data else 0,
            'stock_name': stock_data.get('stock_name', '') if stock_data else '',
            'open_price': 0,
            'high_price': 0,
            'low_price': 0
        }
    
    try:
        df = pd.DataFrame(stock_data['stock_data'])
        
        if len(df) > 0:
            latest_candle = df.iloc[-1]
            current_price = float(latest_candle['close'])
            open_price = float(latest_candle['open'])
            high_price = float(latest_candle['high'])
            low_price = float(latest_candle['low'])
            volume = int(latest_candle['volume']) if 'volume' in latest_candle else 0
            
            # Calculate price change from previous candle
            if len(df) > 1:
                prev_close = float(df.iloc[-2]['close'])
                price_change = ((current_price - prev_close) / prev_close) * 100
            else:
                price_change = 0
        else:
            current_price = stock_data.get('current_price', 0)
            open_price = current_price
            high_price = current_price
            low_price = current_price
            volume = stock_data.get('volume', 0)
            price_change = stock_data.get('price_change', 0)
        
        if len(df) < 14:
            return {
                'rsi': 50,
                'rsi_signal': 'Neutral',
                'ma_signal': 'Neutral',
                'macd_signal': 'Neutral',
                'volume_signal': 'Normal',
                'volume_description': 'Volume dalam kisaran normal',
                'avg_volume': 0,
                'current_price': current_price,
                'price_change': price_change,
                'price_change_pct': price_change / current_price * 100 if current_price != 0 else 0,
                'volume': volume,
                'stock_name': stock_data.get('stock_name', ''),
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price
            }

        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50
        
        if current_rsi > 70:
            rsi_signal = 'Overbought'
        elif current_rsi < 30:
            rsi_signal = 'Oversold'
        else:
            rsi_signal = 'Neutral'
        
        # Moving Average
        ma_20 = df['close'].rolling(window=20).mean()
        current_ma = ma_20.iloc[-1] if not ma_20.empty else df['close'].iloc[-1]
        
        if df['close'].iloc[-1] > current_ma:
            ma_signal = 'Bullish'
        else:
            ma_signal = 'Bearish'
        
        # MACD Analysis
        macd_signal = 'Neutral'  # Placeholder, should be calculated
        
        # Volume signal
        if len(df) >= 20:
            avg_volume = df['volume'].tail(20).mean()
        else:
            avg_volume = df['volume'].mean()
            
        current_volume = volume
        
        if current_volume > avg_volume * 2.0:
            volume_signal = 'Sangat Tinggi'
            volume_description = f"Volume {int(current_volume):,} sangat tinggi (>{int(avg_volume * 2):,})"
        elif current_volume > avg_volume * 1.5:
            volume_signal = 'Tinggi'
            volume_description = f"Volume {int(current_volume):,} tinggi (>{int(avg_volume * 1.5):,})"
        elif current_volume < avg_volume * 0.5:
            volume_signal = 'Rendah'
            volume_description = f"Volume {int(current_volume):,} rendah (<{int(avg_volume * 0.5):,})"
        else:
            volume_signal = 'Normal'
            volume_description = f"Volume {int(current_volume):,} dalam kisaran normal"
        
        return {
            'rsi': round(current_rsi, 2),
            'rsi_signal': rsi_signal,
            'ma_signal': ma_signal,
            'macd_signal': macd_signal,
            'volume_signal': volume_signal,
            'volume_description': volume_description,
            'avg_volume': int(avg_volume),
            'current_price': current_price,
            'price_change': round(price_change, 2),
            'price_change_pct': round(price_change / current_price * 100, 2) if current_price != 0 else 0,
            'volume': volume,
            'stock_name': stock_data.get('stock_name', ''),
            'open_price': open_price,
            'high_price': high_price,
            'low_price': low_price
        }
    
    except Exception as e:
        print(f"❌ Error menghitung technical signals: {e}")
        try:
            df = pd.DataFrame(stock_data['stock_data'])
            if len(df) > 0:
                latest_candle = df.iloc[-1]
                return {
                    'rsi': 50,
                    'rsi_signal': 'N/A',
                    'ma_signal': 'N/A',
                    'macd_signal': 'N/A',
                    'volume_signal': 'N/A',
                    'volume_description': 'Tidak tersedia',
                    'avg_volume': 0,
                    'current_price': float(latest_candle['close']),
                    'price_change': 0,
                    'price_change_pct': 0,
                    'volume': int(latest_candle['volume']) if 'volume' in latest_candle else 0,
                    'stock_name': stock_data.get('stock_name', ''),
                    'open_price': float(latest_candle['open']),
                    'high_price': float(latest_candle['high']),
                    'low_price': float(latest_candle['low'])
                }
        except:
            pass
            
        return {
            'rsi': 0,
            'rsi_signal': 'N/A',
            'ma_signal': 'N/A',
            'macd_signal': 'N/A',
            'volume_signal': 'N/A',
            'volume_description': 'Tidak tersedia',
            'avg_volume': 0,
            'current_price': 0,
            'price_change': 0,
            'price_change_pct': 0,
            'volume': 0,
            'stock_name': '',
            'open_price': 0,
            'high_price': 0,
            'low_price': 0
        }

def is_market_open():
    """Cek apakah pasar sedang buka"""
    now = datetime.now(pytz_timezone('Asia/Jakarta'))
    day = now.weekday()
    hour = now.hour
    minute = now.minute
    
    is_weekday = 0 <= day <= 4
    is_market_hours = (9 <= hour < 16) or (hour == 9 and minute >= 0)
    
    return is_weekday and is_market_hours

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard halaman utama"""
    global data_collector, anomaly_detector
    
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of anomalies per page
    
    selected_stock = request.args.get('stock', 'ADRO.JK')  # Ambil dari query parameter atau default ADRO.JK
    selected_period = request.args.get('period', '1mo')  # Ambil dari query parameter atau default 1mo
    
    print(f"📊 Loading dashboard untuk {selected_stock}, periode {selected_period}")
    
    template_data = {
        'stock_code': selected_stock,
        'current_price': 0,
        'price_change': 0,
        'price_change_pct': 0,
        'volume': 0,
        'stock_data': [],
        'success': False,
        'stock_name': ''
    }
    
    if data_collector:
        template_data = get_stock_data_real_time(selected_stock, selected_period)
    
    if not template_data:
        template_data = {
            'success': False,
            'stock_code': selected_stock,
            'stock_data': [],
            'stock_name': 'Unknown'
        }
    
    if 'stock_data' not in template_data:
        template_data['stock_data'] = []
    if 'success' not in template_data:
        template_data['success'] = False
    
    if data_collector is None:
        print(f"❌ DataCollector tidak tersedia")
        return render_template('dashboard.html', error="Data collector tidak tersedia")
    
    stock_code = template_data.get('stock_code', selected_stock)
    stock_data = template_data.get('stock_data', [])
    current_price = template_data.get('current_price', 0)
    volume = template_data.get('volume', 0)
    
    try:
        if data_collector is None:
            broker_data = pd.DataFrame()
        else:
            broker_data = data_collector.get_broker_summary(stock_code, selected_period)
    except Exception as e:
        print(f"❌ Error mengambil broker data: {e}")
        broker_data = pd.DataFrame()
    
    anomalies = []
    total_anomalies = 0
    total_pages = 1
    if anomaly_detector is not None and anomaly_detector.is_trained:
        try:
            all_anomalies = anomaly_detector.detect_broker_anomalies(broker_data)
            
            total_anomalies = len(all_anomalies)
            total_pages = (total_anomalies + per_page - 1) // per_page  # Ceiling division
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            anomalies = all_anomalies[start_idx:end_idx]
            
            print(f"[v0] Total anomalies detected: {len(all_anomalies)}")
            print(f"[v0] Broker data shape: {broker_data.shape if not broker_data.empty else 'Empty'}")
            
            print(f"[v0] Page {page}/{total_pages}, showing {len(anomalies)} anomalies (from index {start_idx} to {end_idx})")
        except Exception as e:
            print(f"⚠️ Error mendeteksi anomalies: {e}")
            import traceback
            traceback.print_exc()
    else:
        total_anomalies = 0
        total_pages = 1
    
    technical_signals = get_technical_signals_real_time(template_data)
    
    alert_system = AlertSystem()
    alerts = alert_system.generate_alerts(technical_signals, anomalies, 
                                         pd.DataFrame(template_data.get('stock_data', [])) if template_data.get('stock_data') else pd.DataFrame())
    
    template_data['technical_signals'] = technical_signals
    template_data['anomalies'] = anomalies
    template_data['pagination'] = {
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_anomalies': total_anomalies,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }
    template_data['alerts'] = alerts
    template_data['energy_stocks'] = ENERGY_STOCKS
    template_data['stock_code'] = selected_stock
    template_data['period'] = selected_period
    template_data['current_time'] = datetime.now(pytz_timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S')
    template_data['market_open'] = is_market_open()
    template_data['total_anomalies'] = total_anomalies
    template_data['total_pages'] = total_pages
    template_data['current_page'] = page
    
    stock_data = template_data.get('stock_data')
    if stock_data is not None and len(stock_data) > 0:
        template_data['realtime_info'] = {
            'price': template_data['current_price'],
            'volume': template_data['volume'],
            'timestamp': datetime.now(pytz_timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        template_data['realtime_info'] = {
            'price': 0,
            'volume': 0,
            'timestamp': datetime.now(pytz_timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    trading_alert = generate_trading_recommendation(technical_signals)
    
    return render_template('dashboard.html', 
                         **template_data,
                         trading_alert=trading_alert)

@app.route('/watchlist')
@login_required
def watchlist():
    """Halaman watchlist user"""
    user_watchlist = Watchlist.query.filter_by(user_id=current_user.id).all()
    return render_template('watchlist.html', watchlist=user_watchlist, energy_stocks=ENERGY_STOCKS)

@app.route('/add_to_watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    stock_code = request.form['stock_code']
    stock_name = ENERGY_STOCKS.get(stock_code, stock_code)
    
    # Cek apakah sudah ada di watchlist
    existing = Watchlist.query.filter_by(
        user_id=current_user.id, 
        stock_code=stock_code
    ).first()
    
    if not existing:
        watchlist_item = Watchlist(
            user_id=current_user.id,
            stock_code=stock_code,
            stock_name=stock_name,
            added_date=datetime.now(pytz_timezone('Asia/Jakarta'))
        )
        db.session.add(watchlist_item)
        db.session.commit()
        flash(f'{stock_name} berhasil ditambahkan ke watchlist!', 'success')
    else:
        flash(f'{stock_name} sudah ada di watchlist!', 'info')
    
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/remove_from_watchlist/<int:watchlist_id>')
@login_required
def remove_from_watchlist(watchlist_id):
    watchlist_item = Watchlist.query.get_or_404(watchlist_id)
    
    # Pastikan user hanya bisa menghapus watchlist miliknya sendiri
    if watchlist_item.user_id == current_user.id:
        db.session.delete(watchlist_item)
        db.session.commit()
        flash('Saham berhasil dihapus dari watchlist!', 'success')
    
    return redirect(url_for('watchlist'))

@app.route('/api/anomalies/<stock_code>')
@login_required
def get_anomalies(stock_code):
    """API endpoint untuk mendapatkan anomalies realtime"""
    try:
        broker_data = data_collector.get_broker_summary(stock_code, '6mo')
        
        if anomaly_detector is not None and anomaly_detector.is_trained:
            anomalies = anomaly_detector.detect_broker_anomalies(broker_data)
            return jsonify({
                'status': 'success',
                'stock_code': stock_code,
                'anomalies': anomalies,
                'count': len(anomalies)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Model tidak tersedia atau belum di-train'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/chart_data/<stock_code>')
@login_required
def get_chart_data(stock_code):
    """API endpoint untuk chart data dengan stock_code dari URL path"""
    global data_collector
    
    print(f"[v0] Chart API called for {stock_code}")
    
    try:
        if data_collector is None:
            print("[v0] Initializing data_collector in API endpoint")
            init_data_collector()
            
        if data_collector is None:
            print("[v0] ERROR: Data collector tidak None setelah init")
            return jsonify({
                'status': 'error',
                'message': 'Data collector tidak diinisialisasi',
                'data': []
            }), 500
        
        print(f"[v0] Fetching chart data for {stock_code}")
        data = data_collector.get_tradingview_like_data(stock_code)
        
        if data is None or data.empty:
            print(f"[v0] Tidak ada data dikembalikan dari get_tradingview_like_data")
            return jsonify({
                'status': 'error',
                'message': 'Tidak ada data tersedia',
                'data': []
            }), 404
        print(f"[v0] Mendapatkan {len(data)} baris data")
        
        chart_data = []
        for _, row in data.iterrows():
            # Handle both Datetime and Date columns
            timestamp = row.get('Datetime', row.get('Date'))
            
            # Convert to ISO string
            if hasattr(timestamp, 'isoformat'):
                iso_str = timestamp.isoformat()
            else:
                iso_str = str(timestamp)
            
            chart_data.append({
                'x': iso_str,
                'o': float(row['Open']),
                'h': float(row['High']),
                'l': float(row['Low']),
                'c': float(row['Close']),
                'v': int(row.get('Volume', 0))
            })
        
        print(f"[v0] Mengembalikan {len(chart_data)} candele")
        return jsonify({
            'status': 'success',
            'stock_code': stock_code,
            'data': chart_data
        })
        
    except Exception as e:
        print(f"[v0] ERROR dalam endpoint data chart: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': []
        }), 500

@app.route('/api/alerts')
@login_required
def get_all_alerts():
    alert_system = AlertSystem()
    all_alerts = alert_system.get_daily_alerts()
    
    return jsonify({
        'status': 'success',
        'data': all_alerts
    })

@app.route('/api/intraday_data/<stock_code>')
@login_required
def api_intraday_data(stock_code):
    """API endpoint khusus untuk data intraday"""
    try:
        interval = request.args.get('interval', '5m')
        period = request.args.get('period', '1d')
        
        intraday_data = data_collector.get_intraday_data(stock_code, interval, period)
        
        if intraday_data is not None and not intraday_data.empty:
            chart_data = []
            for index, row in intraday_data.iterrows():
                timestamp = row['Datetime'] if 'Datetime' in row else row['Date']
                iso_str = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
                chart_data.append({
                    'x': iso_str,
                    'o': float(row['Open']),
                    'h': float(row['High']),
                    'l': float(row['Low']),
                    'c': float(row['Close']),
                    'v': int(row.get('Volume', 0))
                })
            
            return jsonify({
                'status': 'success',
                'stock_code': stock_code,
                'data': chart_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Tidak ada data intraday tersedia'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Function to generate trading recommendation based on technical signals
def generate_trading_recommendation(technical_signals):
    """Generate BUY/SELL/HOLD recommendation with explanation"""
    try:
        rsi = technical_signals.get('rsi', 50)
        rsi_signal = technical_signals.get('rsi_signal', 'Neutral')
        ma_signal = technical_signals.get('ma_signal', 'Neutral')
        volume_signal = technical_signals.get('volume_signal', 'Normal')
        macd_signal = technical_signals.get('macd_signal', 'Neutral')
        
        score = 0
        reasons = []
        confidence = 0
        
        # RSI Analysis - stronger weight
        if rsi < 30:
            score += 3
            confidence += 25
            reasons.append(f"RSI {rsi:.2f} oversold, potensi reversal naik kuat")
        elif rsi < 40:
            score += 2
            confidence += 15
            reasons.append(f"RSI {rsi:.2f} mendekati oversold, momentum bullish")
        elif rsi > 70:
            score -= 3
            confidence += 25
            reasons.append(f"RSI {rsi:.2f} overbought, potensi koreksi turun")
        elif rsi > 60:
            score -= 2
            confidence += 15
            reasons.append(f"RSI {rsi:.2f} mendekati overbought, hati-hati koreksi")
        else:
            reasons.append(f"RSI {rsi:.2f} dalam zona neutral")
        
        # MA Analysis - medium weight
        if ma_signal == 'Bullish':
            score += 2
            confidence += 20
            reasons.append("Harga di atas MA, trend naik konfirmasi")
        elif ma_signal == 'Bearish':
            score -= 2
            confidence += 20
            reasons.append("Harga di bawah MA, trend bearish aktif")
        
        # MACD Analysis - strong weight for momentum
        if macd_signal == 'Bullish':
            score += 2
            confidence += 20
            reasons.append("MACD bullish crossover, momentum beli kuat")
        elif macd_signal == 'Bearish':
            score -= 2
            confidence += 20
            reasons.append("MACD bearish crossover, momentum jual kuat")
        
        # Volume Analysis - confirmation factor
        if volume_signal in ['Sangat Tinggi', 'Tinggi']:
            if score > 0:
                score += 1
                confidence += 15
                reasons.append("Volume tinggi konfirmasi akumulasi")
            elif score < 0:
                score -= 1
                confidence += 15
                reasons.append("Volume tinggi konfirmasi distribusi")
        elif volume_signal == 'Rendah':
            confidence -= 10
            reasons.append("Volume rendah, sinyal kurang valid")
        
        # Determine recommendation with lower threshold
        if score >= 3:
            recommendation = 'STRONG BUY'
            color = 'success'
            icon = 'fa-arrow-trend-up'
            summary = 'Peluang beli sangat kuat'
            confidence = min(confidence, 95)
        elif score >= 1:
            recommendation = 'BUY'
            color = 'success'
            icon = 'fa-arrow-up'
            summary = 'Sinyal beli terdeteksi'
            confidence = min(confidence, 75)
        elif score <= -3:
            recommendation = 'STRONG SELL'
            color = 'danger'
            icon = 'fa-arrow-trend-down'
            summary = 'Sinyal jual sangat kuat'
            confidence = min(confidence, 95)
        elif score <= -1:
            recommendation = 'SELL'
            color = 'danger'
            icon = 'fa-arrow-down'
            summary = 'Sinyal jual terdeteksi'
            confidence = min(confidence, 75)
        else:
            recommendation = 'HOLD'
            color = 'warning'
            icon = 'fa-hand'
            summary = 'Belum ada sinyal jelas, tunggu konfirmasi'
            confidence = max(confidence, 30)
        
        return {
            'recommendation': recommendation,
            'color': color,
            'icon': icon,
            'summary': summary,
            'reasons': reasons,
            'score': score,
            'confidence': confidence
        }
    except Exception as e:
        print(f"❌ Error menghasilkan rekomendasi: {e}")
        return {
            'recommendation': 'HOLD',
            'color': 'warning',
            'icon': 'fa-hand',
            'summary': 'Tidak dapat menganalisis',
            'reasons': ['Data tidak cukup'],
            'score': 0,
            'confidence': 0
        }

# Helper function for file upload validation
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Profile route
@app.route('/profile')
@login_required
def profile():
    profile_photo = session.get('profile_photo', 'images/default-avatar.jpg')
    return render_template('profile.html', profile_photo=profile_photo)

# Profile update route
@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        # Update basic info
        if request.form.get('username'):
            # Check if username already exists
            existing_user = User.query.filter(User.username == request.form['username'], User.id != current_user.id).first()
            if existing_user:
                flash('Username sudah digunakan', 'error')
                return redirect(url_for('profile'))
            current_user.username = request.form['username']
        
        if request.form.get('email'):
            # Check if email already exists
            existing_user = User.query.filter(User.email == request.form['email'], User.id != current_user.id).first()
            if existing_user:
                flash('Email sudah digunakan', 'error')
                return redirect(url_for('profile'))
            current_user.email = request.form['email']
        
        # Phone and profile photo features disabled until database migration is complete
        
        db.session.commit()
        flash('Profile berhasil diperbarui', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('profile'))

# Change password route
@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Password lama tidak sesuai', 'error')
            return redirect(url_for('profile'))
        
        # Validate new password
        if new_password != confirm_password:
            flash('Password baru tidak cocok', 'error')
            return redirect(url_for('profile'))
        
        if len(new_password) < 6:
            flash('Password minimal 6 karakter', 'error')
            return redirect(url_for('profile'))
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password berhasil diubah', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('profile'))

# Profile photo upload route
@app.route('/profile/upload-photo', methods=['POST'])
@login_required
def upload_profile_photo():
    try:
        if 'photo' not in request.files:
            flash('Tidak ada file yang dipilih', 'error')
            return redirect(url_for('profile'))
        
        file = request.files['photo']
        
        if file.filename == '':
            flash('Tidak ada file yang dipilih', 'error')
            return redirect(url_for('profile'))
        
        if file and allowed_file(file.filename):
            # Create uploads directory if it doesn't exist
            upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'profiles')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(f"user_{current_user.id}_{int(time.time())}_{file.filename}")
            filepath = os.path.join(upload_folder, filename)
            
            # Save file
            file.save(filepath)
            
            # Store relative path in session for now (until database is migrated)
            session['profile_photo'] = f'uploads/profiles/{filename}'
            
            flash('Foto profil berhasil diupload', 'success')
        else:
            flash('File tidak diizinkan', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('profile'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_anomaly_detector()
        init_data_collector()
    app.run(debug=True)
