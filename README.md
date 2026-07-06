# AI-Powered Crop Yield Prediction & Optimization Platform

An interactive, AI-driven platform to predict crop land area requirements using machine learning. Built with a premium glassmorphic dark-theme UI, this platform features an interactive Indian state-to-district drill-down map for geographical crop analysis.

### 🌐 Live Deployment
Access the application on Render here:
👉 **[Live Platform Link](https://ai-powered-crop-yield-prediction-and-az7r.onrender.com)**

---

## ⚡ Features

### 1. Interactive Indian Map Explorer
- **Visual Mapping**: Features a Leaflet-based vector map of India centered on CartoDB Dark Matter tiles.
- **Drill-Down Control**: Hovering highlights states in electric cyan. Clicking a state zooms in and exposes a scrollable grid of corresponding districts.
- **Form Sync**: Bidirectional synchronization dynamically updates form fields from map/grid clicks and highlights the map from form dropdown changes.

### 2. Multi-Algorithm Machine Learning Pipeline
- **Auto Preprocessing**: Drops duplicates, fills numerical NaNs with column median, and fills categorical NaNs with mode.
- **Robust Encoding**: Automatically transforms categorical text strings with LabelEncoder and standardizes numerical features with StandardScaler.
- **Model Selection**: Automatically trains **Random Forest Regressor**, **Decision Tree Regressor**, and **Linear Regression** on the dataset. Selects and serializes the model with the highest $R^2$ score (currently **0.8375** using Random Forest).
- **Data Visualizations**: Compiles 6 distinct analytical charts:
  1. Target variable distribution.
  2. Numerical feature correlation heatmap.
  3. Average crop area by Season.
  4. Average crop area by State.
  5. Trend of crop area over Years.
  6. Box plot of crop area distribution per crop type.

### 3. Glassmorphic User Experience
- Designed with Outfit and JetBrains Mono typography.
- Employs a glassmorphic dashboard styled using translucent variables, glowing border actions, and transition loaders.

---

## 🛠️ Technology Stack
* **Backend**: Python 3.12, Flask, SQLite
* **Machine Learning**: Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn
* **Frontend**: HTML5, Vanilla CSS3 (Stitch Design System), JavaScript, Leaflet.js

---

## 📂 Project Structure
```text
├── data/
│   ├── crop_yield.csv          # Expanded crop dataset (20 crops, 10 states)
│   └── generate_rich_data.py   # Script to generate rich synthetic dataset
├── static/
│   ├── css/
│   │   └── style.css           # Custom glassmorphic styling sheet
│   ├── js/
│   │   ├── main.js             # Form validation & animations
│   │   ├── map.js              # Leaflet Map & state-district grid logic
│   │   ├── india.json          # GeoJSON boundaries of India
│   │   └── states-and-districts.json # Indian states to districts mapping
│   └── models/
│       ├── best_model.pkl      # Pickled optimal ML model
│       └── model_metadata.pkl  # Metadata for preprocessing columns & choices
├── templates/
│   ├── base.html               # Main base layout with navbar & footer
│   ├── home.html               # Signin/Signup gatekeeper panels
│   ├── user.html               # Form parameter entry & Leaflet Map explorer
│   ├── result.html             # Prediction outcome & recommendations
│   └── admin*.html             # Admin controls for models, users, and logs
├── app.py                      # Primary Flask application router
├── database.py                 # SQLite tables setup & queries
├── ml_engine.py                # Preprocessing & training pipeline
└── test_app.py                 # Integration testing suite
```

---

## 🚀 Running Locally

### 1. Prerequisite Installation
Ensure you have Python 3.12+ installed. Set up the virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Launch the Application
Start the Flask dev server:
```powershell
python app.py
```
Open `http://127.0.0.1:5000` in your web browser.

---

## 🔑 Access Credentials

### Regular User Login
Create a fresh account on the **User Signup** page or use:
* **Username**: `test_farmer_99`
* **Email**: `farmer99@gmail.com`
* **Password**: `Amma@1234`
*(Note: Live Render databases start empty; register a new account on the live signup tab to access the dashboard).*

### Admin Login
* **Username**: `admin`
* **Password**: `admin` or `adminpassword123`