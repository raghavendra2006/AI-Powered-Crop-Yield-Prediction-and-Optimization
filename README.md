# 🌾 AI-Powered Crop Yield Prediction & Optimization

An end-to-end web application powered by **Machine Learning** and **Flask** designed to predict crop yields, evaluate multiple ML algorithms, auto-generate interactive visualizations, provide tailored agronomic recommendations, and track prediction history for farmers and agricultural managers.

---

## 🌟 Features

- **🤖 Automated ML Pipeline**: Train and compare multiple regression models (**Random Forest**, **Gradient Boosting**, **Linear Regression**) on custom uploaded agricultural datasets (`.csv`, `.xlsx`, `.xls`, `.txt`).
- **🎯 Accurate Yield Prediction**: Input environmental, soil, geographic, and agricultural parameters (rainfall, temperature, humidity, fertilizer, area, crop type, soil type, coordinates) to receive instant yield predictions.
- **💡 Smart Agronomic Recommendations**: Rule-based expert suggestions dynamically generated based on prediction results and climate/soil thresholds (e.g., drip irrigation alerts, mulching, organic compost tips).
- **📊 Interactive Data Visualizations**: Auto-generates 6 statistical charts for dataset insights (Target Distribution, Correlation Heatmap, Feature Box Plots, Categorical Counts, Feature Scatter Plots, Subplot Grid).
- **🗺️ Leaflet.js GIS Integration**: Interactive map selector to dynamically pinpoint field coordinates (Latitude & Longitude).
- **👥 Role-Based Access Control (RBAC)**:
  - **User Portal**: Registration, login, dataset upload & model training, crop yield prediction, history tracking.
  - **Admin Portal**: System-wide dashboard, global user management, system-wide yield prediction oversight.
- **💾 SQLite Persistent Storage**: Dedicated SQLite databases for user authentication (`signup.db`) and prediction history (`previous_results.db`).

---

## 🛠️ Tech Stack

### **Backend & Machine Learning**
- **Python 3.10+**
- **Flask** (Web Framework & Session Management)
- **Scikit-Learn** (Random Forest, Gradient Boosting, Linear Regression, Metrics: $R^2$, MSE, MAE)
- **Pandas & NumPy** (Data Preprocessing, Encoding, Feature Engineering)
- **Joblib** (Model Serialization & Persistence)
- **Gunicorn** (Production WSGI Web Server)

### **Frontend & Visualization**
- **HTML5 & Vanilla CSS** (Responsive Dark Theme UI, Glassmorphism, Micro-animations)
- **Matplotlib & Seaborn** (Dynamic Base64 Visualizations)
- **Leaflet.js** (Interactive OpenStreetMap GIS Map Selector)

### **Database**
- **SQLite3** (`signup.db`, `previous_results.db`)

---

## 📁 Repository Structure

```
├── app.py                     # Main Flask application logic, ML pipelines & DB initializers
├── requirements.txt           # Python package dependencies
├── Procfile                   # Process configuration for Gunicorn/Render deployment
├── signup.db                  # SQLite database for user registration & authentication
├── previous_results.db        # SQLite database for prediction history
├── models/                    # Directory for serialized trained ML models (.joblib)
├── uploads/                   # Directory for uploaded user datasets
├── static/
│   ├── css/
│   │   └── style.css          # Global styling, responsive dark theme & components
│   └── js/
│       └── map.js             # Leaflet.js map integration logic
└── templates/                 # Jinja2 HTML templates
    ├── home.html              # Landing page
    ├── signup.html            # User registration template
    ├── signin_user.html       # User authentication template
    ├── signin_admin.html      # Admin authentication template
    ├── user_page.html         # User dashboard
    ├── upload_train.html      # Dataset upload & ML model training interface
    ├── result_page.html       # Prediction results & agronomic advice template
    ├── previous_results.html  # Historical prediction log
    ├── admin_page.html        # Admin control panel
    ├── admin_users.html       # Admin user management view
    └── admin_results.html     # Admin global prediction oversight view
```

---

## ⚙️ Local Installation & Setup

### **Prerequisites**
- Python 3.10 or higher
- Git

### **1. Clone the Repository**
```bash
git clone https://github.com/raghavendra2006/AI-Powered-Crop-Yield-Prediction-and-Optimization.git
cd AI-Powered-Crop-Yield-Prediction-and-Optimization
```

### **2. Create and Activate Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Run the Application**
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.


## 🔐 Credentials (Default Admin)

- **Admin Username**: `admin`
- **Admin Password**: `Admin@123`

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.