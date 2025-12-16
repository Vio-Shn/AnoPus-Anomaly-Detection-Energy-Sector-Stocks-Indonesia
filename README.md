<div align="center">
  # 🚀 AnoPus
  ### AI-Powered Trading Intelligence Platform
  
  <p align="center">
    <strong>Deteksi Anomali Pasar Sebelum Trader Lain</strong>
    <br />
    Platform trading intelligence berbasis machine learning untuk mendeteksi peluang trading di sektor energi Indonesia dengan akurasi tinggi.
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/Flask-3.0+-green.svg" alt="Flask">
    <img src="https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg" alt="Tailwind">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
    <img src="https://img.shields.io/badge/Status-Active-success.svg" alt="Status">
  </p>
</div>

---
---

## ✨ Fitur Utama

### 🤖 AI & Machine Learning
- **Anomaly Detection**: Deteksi anomali trading menggunakan Isolation Forest algorithm
- **Technical Analysis**: Analisis RSI, Moving Average, MACD, dan Volume signals
- **Smart Alerts**: Sistem rekomendasi trading otomatis berdasarkan sinyal teknis

### 📈 Real-Time Data
- **Live Stock Data**: Integrasi dengan Yahoo Finance API
- **Broker Analysis**: Analisis aktivitas broker secara real-time
- **Interactive Charts**: Grafik harga interaktif dengan LightweightCharts
- **Auto-refresh**: Update data otomatis saat market buka

### 🎯 Energy Sector Focus
- **30+ Saham Energi**: Coverage lengkap sektor energi Indonesia
- **Real-Time Updates**: Data update 99.8% akurasi
- **Historical Data**: Akses data historis hingga 6 bulan

### 💼 User Management
- **Secure Authentication**: Login/Register dengan Flask-Login
- **Watchlist**: Simpan dan monitor saham favorit
- **Profile Management**: Upload foto profil dan kelola informasi pribadi
- **Session Management**: Secure session handling dengan bcrypt

### 📱 Responsive Design
- **Mobile-First**: Optimized untuk semua device
- **Tailwind CSS**: Modern utility-first CSS framework
- **Glassmorphism UI**: Beautiful card-based design dengan backdrop blur
- **Dark Theme**: Eye-friendly dark color scheme

---

## 🛠️ Tech Stack

### Backend
```
Python 3.10+          # Core language
Flask 3.0+            # Web framework
Flask-Login           # Authentication
SQLAlchemy            # ORM database
Pandas & NumPy        # Data processing
Scikit-learn          # Machine learning
YFinance              # Stock data API
```

### Frontend
```
HTML5 & CSS3          # Structure & styling
Tailwind CSS 3.4      # Utility-first CSS
JavaScript ES6+       # Interactivity
Font Awesome 6        # Icons
LightweightCharts     # Interactive charts
```

### Database
```
SQLite                # Development database
PostgreSQL ready      # Production ready
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone repository**
```bash
git clone https://github.com/yourusername/anopus.git
cd anopus
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
python recreate_database.py
```

5. **Train anomaly detection model**
```bash
python scripts/train_anomaly_model.py
```

6. **Run application**
```bash
python app.py
```

7. **Open browser**
```
http://localhost:5000
```

---

## 📂 Project Structure

```
anopus/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── modules/
│   ├── anomaly_detector.py    # Anomaly detection ML model
│   ├── data_collector.py      # Stock data collector
│   ├── technical_analyzer.py  # Technical indicators
│   └── alert_system.py        # Alert generation system
├── templates/
│   ├── base.html              # Base template
│   ├── landing.html           # Landing page
│   ├── dashboard.html         # Main dashboard
│   ├── login.html             # Login page
│   ├── register.html          # Register page
│   ├── profile.html           # User profile
│   └── watchlist.html         # Watchlist page
├── static/
│   ├── css/                   # Stylesheets
│   └── images/                # Static images
├── scripts/
│   ├── train_anomaly_model.py # Model training script
│   └── migrate_db.py          # Database migration
└── README.md                  # This file
```

---

## 🎓 How It Works

### 1. Data Collection
AnoPus menggunakan **Yahoo Finance API** untuk mengambil data saham real-time dan historis dari sektor energi Indonesia. Data disimpan dalam database SQLite untuk fallback ketika API rate limit.

### 2. Anomaly Detection
Model **Isolation Forest** digunakan untuk mendeteksi anomali pada:
- Volume trading yang tidak biasa
- Aktivitas broker mencurigakan
- Pergerakan harga abnormal
- Volatilitas tinggi

### 3. Technical Analysis
Sistem menghitung berbagai indikator teknis:
- **RSI (Relative Strength Index)**: Overbought/Oversold signals
- **Moving Averages**: Trend identification
- **MACD**: Momentum analysis
- **Volume Analysis**: Trading volume patterns

### 4. Smart Alerts
Berdasarkan analisis teknis dan deteksi anomali, sistem menghasilkan rekomendasi trading:
- 🔴 **STRONG SELL**: Multiple bearish signals
- 🟠 **SELL**: Bearish signals detected
- 🟡 **HOLD**: Neutral signals
- 🟢 **BUY**: Bullish signals detected
- 💚 **STRONG BUY**: Multiple bullish signals

---

## 📊 API Endpoints

### Authentication
```
POST   /login              # User login
POST   /register           # User registration
GET    /logout             # User logout
```

### Dashboard
```
GET    /dashboard          # Main dashboard
GET    /api/chart_data     # Chart data API
GET    /api/anomalies      # Anomalies data API
```

### Watchlist
```
GET    /watchlist          # User watchlist
POST   /api/add_watchlist  # Add stock to watchlist
DELETE /api/remove_watchlist # Remove from watchlist
```

### Profile
```
GET    /profile            # User profile page
POST   /update_profile     # Update profile info
POST   /change_password    # Change password
```

---

## 🔒 Security Features

- ✅ Password hashing dengan bcrypt
- ✅ Secure session management
- ✅ SQL injection prevention dengan parameterized queries
- ✅ CSRF protection
- ✅ Input validation dan sanitization
- ✅ Environment variables untuk sensitive data

---

## 📱 Responsive Breakpoints

```css
Mobile:  < 640px   (sm)
Tablet:  640-1024px (md/lg)
Desktop: > 1024px  (xl)
```

Semua halaman fully responsive dengan mobile-first approach menggunakan Tailwind CSS breakpoints.

---

## 🤝 Contributing

Kontribusi sangat diterima! Berikut cara contribute:

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---
---

## 👨‍💻 Author

**Your Name**
- GitHub: [@vioshn](https://github.com/Vio-Shn)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/viona-siahaan)

---

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Yahoo Finance](https://finance.yahoo.com/) - Stock data provider
- [LightweightCharts](https://www.tradingview.com/lightweight-charts/) - Chart library
- [Font Awesome](https://fontawesome.com/) - Icon library
- [Scikit-learn](https://scikit-learn.org/) - Machine learning library

---

<div align="center">
  <p>Made with ❤️ for Indonesian Traders</p>
  <p>⭐ Star this repo if you find it useful!</p>
</div>
