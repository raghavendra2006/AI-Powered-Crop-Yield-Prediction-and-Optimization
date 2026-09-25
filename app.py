"""
AI-Powered Crop Yield Prediction & Optimization
Flask Application — app.py
"""

import os
import io
import base64
import sqlite3
import joblib
import warnings
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from flask import (Flask, render_template, request, redirect,
            url_for, session, flash, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

warnings.filterwarnings('ignore')

# ── App Config ──────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'crop_yield_secret_key_2024'

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
MODEL_FOLDER  = os.path.join(os.path.dirname(__file__), 'models')
ALLOWED_EXT   = {'csv', 'xlsx', 'xls', 'txt'}
ADMIN_USER    = 'admin'
ADMIN_PASS    = 'Admin@123'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER,  exist_ok=True)

# ── Database Paths ──────────────────────────────────────────
SIGNUP_DB  = os.path.join(os.path.dirname(__file__), 'signup.db')
RESULT_DB  = os.path.join(os.path.dirname(__file__), 'previous_results.db')

# ── DB Init ─────────────────────────────────────────────────
def init_dbs():
    # signup.db
    con = sqlite3.connect(SIGNUP_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            username  TEXT    UNIQUE NOT NULL,
            email     TEXT    UNIQUE NOT NULL,
            phone     TEXT    NOT NULL,
            password  TEXT    NOT NULL,
            created_at TEXT   DEFAULT CURRENT_TIMESTAMP
        )""")
    con.commit(); con.close()

    # previous_results.db
    con = sqlite3.connect(RESULT_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT,
            crop_type     TEXT,
            season        TEXT,
            soil_type     TEXT,
            area          REAL,
            rainfall      REAL,
            temperature   REAL,
            humidity      REAL,
            fertilizer    REAL,
            pesticide     REAL,
            latitude      REAL,
            longitude     REAL,
            predicted_yield REAL,
            suggestion    TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
    con.commit(); con.close()

init_dbs()

# ── Helpers ─────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight',
                facecolor='#0f1923', edgecolor='none', dpi=110)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_b64

def get_suggestions(crop_type, predicted_yield, area, rainfall, temperature, humidity, fertilizer):
    tips = []
    if predicted_yield < 1000:
        tips.append("🌱 Consider soil enrichment with organic compost to boost yield potential.")
    if rainfall < 500:
        tips.append("💧 Install drip irrigation — rainfall is below optimal levels for this crop.")
    if temperature > 35:
        tips.append("🌡️ Use shade nets or heat-resistant crop varieties to mitigate high temperatures.")
    if humidity < 40:
        tips.append("💦 Increase humidity with mulching techniques to retain soil moisture.")
    if fertilizer < 50:
        tips.append("🌾 Increase NPK fertilizer application according to soil test recommendations.")
    if area > 10:
        tips.append("🚜 Mechanized harvesting is recommended for large area — reduces labor cost by 40%.")
    tips.append(f"📊 For {crop_type}, intercropping with legumes can improve nitrogen fixation.")
    tips.append("🔄 Rotate crops each season to prevent soil nutrient depletion.")
    return tips

def make_visualizations(df, target_col):
    """Generate 6 visualizations and return list of base64 images with titles."""
    charts = []
    plt.style.use('dark_background')
    COLORS = ['#00d084', '#7c3aed', '#06b6d4', '#f59e0b', '#ef4444', '#10b981']

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # 1. Distribution of target
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df[target_col].dropna(), bins=30, color='#00d084', alpha=0.8, edgecolor='#0f1923')
    ax.set_xlabel(target_col, color='#8ca0bc'); ax.set_ylabel('Count', color='#8ca0bc')
    ax.set_title(f'Distribution of {target_col}', color='#f0f6ff', fontweight='bold')
    ax.tick_params(colors='#8ca0bc'); fig.patch.set_facecolor('#0f1923'); ax.set_facecolor('#162030')
    charts.append(('Target Distribution', fig_to_b64(fig)))

    # 2. Correlation Heatmap
    if len(num_cols) > 1:
        fig, ax = plt.subplots(figsize=(8, 6))
        corr = df[num_cols[:10]].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        cmap = sns.diverging_palette(145, 300, s=80, l=40, as_cmap=True)
        sns.heatmap(corr, mask=mask, cmap=cmap, annot=True, fmt='.2f',
                    ax=ax, linewidths=0.5, linecolor='#0f1923',
                    annot_kws={'size': 7, 'color': 'white'})
        ax.set_title('Feature Correlation Heatmap', color='#f0f6ff', fontweight='bold')
        ax.tick_params(colors='#8ca0bc'); fig.patch.set_facecolor('#0f1923'); ax.set_facecolor('#162030')
        plt.tight_layout()
        charts.append(('Correlation Heatmap', fig_to_b64(fig)))

    # 3. Box Plots for numeric features
    if len(num_cols) >= 2:
        cols_to_plot = [c for c in num_cols if c != target_col][:5]
        if cols_to_plot:
            fig, axes = plt.subplots(1, len(cols_to_plot), figsize=(max(8, 2.5*len(cols_to_plot)), 4))
            if len(cols_to_plot) == 1: axes = [axes]
            for i, col in enumerate(cols_to_plot):
                bp = axes[i].boxplot(df[col].dropna(), patch_artist=True,
                                     boxprops=dict(facecolor=COLORS[i % len(COLORS)], alpha=0.7),
                                     medianprops=dict(color='white', linewidth=2))
                axes[i].set_title(col, color='#8ca0bc', fontsize=9)
                axes[i].tick_params(colors='#8ca0bc'); axes[i].set_facecolor('#162030')
            fig.patch.set_facecolor('#0f1923')
            fig.suptitle('Box Plots — Feature Spread', color='#f0f6ff', fontweight='bold', y=1.02)
            plt.tight_layout()
            charts.append(('Box Plots', fig_to_b64(fig)))

    # 4. Bar chart — category counts (first categorical col)
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        col = cat_cols[0]
        counts = df[col].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(counts.index, counts.values, color=COLORS[:len(counts)], edgecolor='#0f1923')
        ax.set_xlabel(col, color='#8ca0bc'); ax.set_ylabel('Count', color='#8ca0bc')
        ax.set_title(f'Category Distribution — {col}', color='#f0f6ff', fontweight='bold')
        ax.tick_params(colors='#8ca0bc', axis='x', rotation=30)
        fig.patch.set_facecolor('#0f1923'); ax.set_facecolor('#162030')
        plt.tight_layout()
        charts.append((f'{col} Counts', fig_to_b64(fig)))

    # 5. Scatter — first numeric feature vs target
    feat_cols = [c for c in num_cols if c != target_col]
    if feat_cols:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.scatter(df[feat_cols[0]], df[target_col], alpha=0.5, color='#06b6d4', s=15, edgecolors='none')
        ax.set_xlabel(feat_cols[0], color='#8ca0bc'); ax.set_ylabel(target_col, color='#8ca0bc')
        ax.set_title(f'{feat_cols[0]} vs {target_col}', color='#f0f6ff', fontweight='bold')
        ax.tick_params(colors='#8ca0bc'); fig.patch.set_facecolor('#0f1923'); ax.set_facecolor('#162030')
        plt.tight_layout()
        charts.append((f'{feat_cols[0]} vs {target_col}', fig_to_b64(fig)))

    # 6. Pairplot-style (top 4 numeric vs target as subplots)
    top_feats = [c for c in num_cols if c != target_col][:4]
    if len(top_feats) >= 2:
        fig, axes = plt.subplots(1, len(top_feats), figsize=(max(8, 3*len(top_feats)), 4))
        if len(top_feats) == 1: axes = [axes]
        for i, feat in enumerate(top_feats):
            axes[i].scatter(df[feat], df[target_col], alpha=0.4, color=COLORS[i % len(COLORS)], s=10)
            axes[i].set_xlabel(feat, color='#8ca0bc', fontsize=8)
            axes[i].set_ylabel(target_col if i == 0 else '', color='#8ca0bc', fontsize=8)
            axes[i].tick_params(colors='#8ca0bc', labelsize=7); axes[i].set_facecolor('#162030')
        fig.patch.set_facecolor('#0f1923')
        fig.suptitle('Feature vs Target Scatter Matrix', color='#f0f6ff', fontweight='bold')
        plt.tight_layout()
        charts.append(('Scatter Matrix', fig_to_b64(fig)))

    return charts

# ── Route: Home ─────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

# ── Route: Signup ────────────────────────────────────────────
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        errors = []
        if not all([name, username, email, phone, password, confirm]):
            errors.append('All fields are required.')
        if not email.endswith('@gmail.com'):
            errors.append('Email must be a @gmail.com address.')
        if not (phone.isdigit() and len(phone) == 10):
            errors.append('Phone must be 10 digits (without +91).')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        if errors:
            return render_template('signup.html', errors=errors,
                                   form_data=request.form)

        hashed = generate_password_hash(password)
        try:
            con = sqlite3.connect(SIGNUP_DB)
            con.execute(
                "INSERT INTO users (name,username,email,phone,password) VALUES (?,?,?,?,?)",
                (name, username, email, phone, hashed))
            con.commit(); con.close()
            flash('Account created successfully! Please sign in.', 'success')
            return redirect(url_for('signin_user'))
        except sqlite3.IntegrityError:
            return render_template('signup.html',
                                   errors=['Username or email already exists.'],
                                   form_data=request.form)
    return render_template('signup.html', errors=[], form_data={})

# ── Route: Signin User ──────────────────────────────────────
@app.route('/signin_user', methods=['GET', 'POST'])
def signin_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        con = sqlite3.connect(SIGNUP_DB)
        row = con.execute(
            "SELECT * FROM users WHERE username=? AND email=?",
            (username, email)).fetchone()
        con.close()

        if row and check_password_hash(row[5], password):
            session['username'] = username
            session['role']     = 'user'
            return redirect(url_for('user_page'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('signin_user.html')

# ── Route: Signin Admin ─────────────────────────────────────
@app.route('/signin_admin', methods=['GET', 'POST'])
def signin_admin():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['username'] = username
            session['role']     = 'admin'
            return redirect(url_for('admin_page'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('signin_admin.html')

# ── Route: User Page ────────────────────────────────────────
@app.route('/user_page', methods=['GET', 'POST'])
def user_page():
    if session.get('role') != 'user':
        return redirect(url_for('signin_user'))

    if request.method == 'POST':
        try:
            crop_type   = request.form.get('crop_type', 'Unknown')
            season      = request.form.get('season', 'Kharif')
            soil_type   = request.form.get('soil_type', 'Loamy')
            area        = float(request.form.get('area', 1))
            rainfall    = float(request.form.get('rainfall', 800))
            temperature = float(request.form.get('temperature', 25))
            humidity    = float(request.form.get('humidity', 60))
            fertilizer  = float(request.form.get('fertilizer', 50))
            pesticide   = float(request.form.get('pesticide', 1))
            latitude    = float(request.form.get('latitude', 20.5937))
            longitude   = float(request.form.get('longitude', 78.9629))

            # Load model
            model_path = os.path.join(MODEL_FOLDER, 'crop_model.pkl')
            meta_path  = os.path.join(MODEL_FOLDER, 'model_meta.pkl')

            if os.path.exists(model_path) and os.path.exists(meta_path):
                model = joblib.load(model_path)
                meta  = joblib.load(meta_path)
                le_map    = meta.get('label_encoders', {})
                scaler    = meta.get('scaler')
                feature_cols = meta.get('feature_cols', [])
                cat_map   = meta.get('cat_map', {})

                # Build input row
                input_dict = {
                    'Crop_Type': crop_type, 'Season': season, 'Soil_Type': soil_type,
                    'Area': area, 'Rainfall': rainfall, 'Temperature': temperature,
                    'Humidity': humidity, 'Fertilizer': fertilizer, 'Pesticide': pesticide,
                }
                row = []
                for col in feature_cols:
                    val = input_dict.get(col, 0)
                    if col in le_map:
                        le = le_map[col]
                        classes = list(le.classes_)
                        if val in classes:
                            val = le.transform([val])[0]
                        else:
                            val = 0
                    row.append(float(val))

                X_pred = np.array(row).reshape(1, -1)
                if scaler:
                    X_pred = scaler.transform(X_pred)
                predicted_yield = float(model.predict(X_pred)[0])
            else:
                # Fallback simple formula
                predicted_yield = round(
                    area * (rainfall * 0.003 + temperature * 0.5 + humidity * 0.4
                            + fertilizer * 0.8 - pesticide * 2 + 200), 2)

            predicted_yield = round(max(0, predicted_yield), 2)

            suggestions = get_suggestions(crop_type, predicted_yield, area,
                                          rainfall, temperature, humidity, fertilizer)

            # Save to DB
            con = sqlite3.connect(RESULT_DB)
            con.execute("""INSERT INTO results
                (username,crop_type,season,soil_type,area,rainfall,temperature,
                 humidity,fertilizer,pesticide,latitude,longitude,predicted_yield,suggestion)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (session['username'], crop_type, season, soil_type, area,
                 rainfall, temperature, humidity, fertilizer, pesticide,
                 latitude, longitude, predicted_yield, ' | '.join(suggestions)))
            con.commit(); con.close()

            session['last_result'] = {
                'crop_type': crop_type, 'season': season, 'soil_type': soil_type,
                'area': area, 'rainfall': rainfall, 'temperature': temperature,
                'humidity': humidity, 'fertilizer': fertilizer, 'pesticide': pesticide,
                'latitude': latitude, 'longitude': longitude,
                'predicted_yield': predicted_yield, 'suggestions': suggestions
            }
            return redirect(url_for('result_page'))

        except Exception as e:
            flash(f'Error during prediction: {str(e)}', 'danger')

    return render_template('user_page.html', username=session.get('username'))

# ── Route: Result Page ──────────────────────────────────────
@app.route('/result')
def result_page():
    if session.get('role') != 'user':
        return redirect(url_for('signin_user'))
    result = session.get('last_result')
    if not result:
        return redirect(url_for('user_page'))
    return render_template('result_page.html', result=result, username=session.get('username'))

# ── Route: Previous Results (User) ──────────────────────────
@app.route('/previous_results')
def previous_results():
    if session.get('role') != 'user':
        return redirect(url_for('signin_user'))
    con = sqlite3.connect(RESULT_DB)
    rows = con.execute(
        "SELECT * FROM results WHERE username=? ORDER BY id DESC",
        (session['username'],)).fetchall()
    con.close()
    return render_template('previous_results.html', rows=rows, username=session.get('username'))

# ── Route: Admin Page ───────────────────────────────────────
@app.route('/admin_page')
def admin_page():
    if session.get('role') != 'admin':
        return redirect(url_for('signin_admin'))
    return render_template('admin_page.html')

# ── Route: Upload & Train ────────────────────────────────────
@app.route('/upload_train', methods=['GET', 'POST'])
def upload_train():
    if session.get('role') != 'admin':
        return redirect(url_for('signin_admin'))

    context = {}

    if request.method == 'POST':
        file = request.files.get('dataset')
        if not file or file.filename == '':
            flash('No file selected.', 'danger')
            return render_template('upload_train.html', **context)
        if not allowed_file(file.filename):
            flash('Unsupported format. Use CSV, Excel, or TXT.', 'danger')
            return render_template('upload_train.html', **context)

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            # Load data
            ext = filename.rsplit('.', 1)[1].lower()
            if ext == 'csv':
                df = pd.read_csv(filepath)
            elif ext in ('xlsx', 'xls'):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath, sep=None, engine='python')

            raw_shape = df.shape

            # ── Preprocessing ──
            df.columns = df.columns.str.strip()
            df.drop_duplicates(inplace=True)
            for col in df.columns:
                if df[col].dtype == object:
                    df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown', inplace=True)
                else:
                    df[col].fillna(df[col].median(), inplace=True)

            clean_shape = df.shape
            target_col  = df.columns[-1]
            feature_cols = list(df.columns[:-1])

            # ── Visualizations ──
            charts = make_visualizations(df, target_col)

            # ── Feature Engineering ──
            cat_cols = df[feature_cols].select_dtypes(include=['object']).columns.tolist()
            le_map   = {}
            for col in cat_cols:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                le_map[col] = le

            X = df[feature_cols].values
            y = df[target_col].values

            # Scale
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Encode y if categorical
            if df[target_col].dtype == object:
                le_y = LabelEncoder()
                y = le_y.fit_transform(y.astype(str))
            else:
                le_y = None

            # Split
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42)

            # ── Train 3 Models ──
            models_def = [
                ('Random Forest',       RandomForestRegressor(n_estimators=100, random_state=42)),
                ('Gradient Boosting',   GradientBoostingRegressor(n_estimators=100, random_state=42)),
                ('Linear Regression',   LinearRegression()),
            ]

            results = []
            best_r2 = -np.inf
            best_model = None

            for name, mdl in models_def:
                mdl.fit(X_train, y_train)
                y_pred = mdl.predict(X_test)
                r2   = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae  = mean_absolute_error(y_test, y_pred)
                results.append({'name': name, 'r2': round(r2*100, 2), 'rmse': round(rmse, 2), 'mae': round(mae, 2)})
                if r2 > best_r2:
                    best_r2 = r2; best_model = (name, mdl)

            # Mark best
            for r in results:
                r['is_best'] = (r['name'] == best_model[0])

            # Save best model + metadata
            joblib.dump(best_model[1], os.path.join(MODEL_FOLDER, 'crop_model.pkl'))
            joblib.dump({
                'label_encoders': le_map,
                'scaler': scaler,
                'feature_cols': feature_cols,
                'target_col': target_col,
            }, os.path.join(MODEL_FOLDER, 'model_meta.pkl'))

            context = {
                'trained': True,
                'filename': filename,
                'raw_shape': raw_shape,
                'clean_shape': clean_shape,
                'target_col': target_col,
                'feature_cols': feature_cols,
                'charts': charts,
                'model_results': results,
                'best_model': best_model[0],
                'best_r2': round(best_r2 * 100, 2),
                'train_size': len(X_train),
                'test_size': len(X_test),
            }

        except Exception as e:
            flash(f'Training failed: {str(e)}\n{traceback.format_exc()}', 'danger')

    return render_template('upload_train.html', **context)

# ── Route: Admin — All Results ───────────────────────────────
@app.route('/admin_results')
def admin_results():
    if session.get('role') != 'admin':
        return redirect(url_for('signin_admin'))
    con = sqlite3.connect(RESULT_DB)
    rows = con.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
    con.close()
    return render_template('admin_results.html', rows=rows)

# ── Route: Admin — User Details ─────────────────────────────
@app.route('/admin_users')
def admin_users():
    if session.get('role') != 'admin':
        return redirect(url_for('signin_admin'))
    con = sqlite3.connect(SIGNUP_DB)
    rows = con.execute("SELECT id,name,username,email,phone,created_at FROM users ORDER BY id DESC").fetchall()
    con.close()
    return render_template('admin_users.html', rows=rows)

# ── Route: Logout ────────────────────────────────────────────
@app.route('/logout')
def logout():
    role = session.get('role')
    session.clear()
    if role == 'admin':
        return redirect(url_for('signin_admin'))
    return redirect(url_for('signin_user'))

# ── Run ──────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
