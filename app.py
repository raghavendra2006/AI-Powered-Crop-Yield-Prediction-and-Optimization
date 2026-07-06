import os
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import database
import ml_engine

app = Flask(__name__)
app.secret_key = "crop_yield_prediction_secret_key_123#"
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpassword123"

def login_required(role="user"):
    """Decorator-like helper to check session roles."""
    if "username" not in session:
        return False
    if role == "admin" and not session.get("is_admin", False):
        return False
    return True

@app.before_request
def seed_default_model_if_missing():
    """Seeds the database and trains default model on startup if not present."""
    # Ensure database is initialized
    database.init_dbs()
    
    best_model_path = os.path.join(ml_engine.MODEL_DIR, "best_model.pkl")
    metadata_path = os.path.join(ml_engine.MODEL_DIR, "model_metadata.pkl")
    
    if not os.path.exists(best_model_path) or not os.path.exists(metadata_path):
        print("No pre-trained model found. Seeding default model using data/crop_yield.csv...")
        default_csv = os.path.join("data", "crop_yield.csv")
        if os.path.exists(default_csv):
            try:
                df = ml_engine.load_dataset(default_csv)
                cleaned_df = ml_engine.preprocess_data(df)
                feature_cols = ["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Production"]
                target_col = "Area"
                # Train and save
                ml_engine.generate_visualizations(cleaned_df, target_col)
                ml_engine.train_and_save_model(cleaned_df, feature_cols, target_col, scaler_type="standard")
                print("Default model seeded successfully!")
            except Exception as e:
                print(f"Error seeding default model: {e}")
        else:
            print("Warning: data/crop_yield.csv not found. Admin must train model manually.")

@app.route("/")
def home():
    if "username" in session:
        if session.get("is_admin"):
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("predict"))
    return render_template("home.html")

@app.route("/signup", methods=["POST"])
def user_signup():
    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    # Serverside Validations
    if not email.endswith("@gmail.com"):
        flash("Email must end with @gmail.com", "danger")
        return redirect(url_for("home", tab="signup"))
        
    # Phone must start with +91 and contain 10 digit number
    import re
    if not re.match(r"^\+91\s?\d{10}$", phone):
        flash("Phone number must be +91 followed by 10 digits", "danger")
        return redirect(url_for("home", tab="signup"))
        
    # Password requirement check (at least 8 chars, 1 upper, 1 lower, 1 digit, 1 special)
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
        flash("Password does not meet complexity requirements.", "danger")
        return redirect(url_for("home", tab="signup"))
        
    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("home", tab="signup"))
        
    success = database.add_user(name, username, email, phone, password)
    if success:
        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("home", tab="signin"))
    else:
        flash("Username is already taken. Please choose another one.", "danger")
        return redirect(url_for("home", tab="signup"))

@app.route("/login/user", methods=["POST"])
def user_login():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    
    user = database.authenticate_user(username, email, password)
    if user:
        session["username"] = user["username"]
        session["is_admin"] = False
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("predict"))
    else:
        flash("Invalid username, email, or password.", "danger")
        return redirect(url_for("home", tab="signin"))

@app.route("/login/admin", methods=["POST"])
def admin_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    if username == ADMIN_USERNAME and (password == ADMIN_PASSWORD or password == "admin"):
        session["username"] = "admin"
        session["is_admin"] = True
        flash("Admin session established.", "success")
        return redirect(url_for("admin_dashboard"))
    else:
        flash("Invalid Admin credentials.", "danger")
        return redirect(url_for("home", tab="admin"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("home"))

@app.route("/predict", methods=["GET", "POST"])
def predict():
    if not login_required("user"):
        flash("Please log in as a user to access the prediction portal.", "danger")
        return redirect(url_for("home"))
        
    metadata = None
    metadata_path = os.path.join(ml_engine.MODEL_DIR, "model_metadata.pkl")
    if os.path.exists(metadata_path):
        import pickle
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
            
    if request.method == "POST":
        if not metadata:
            flash("No model configured. Prediction aborted.", "danger")
            return redirect(url_for("predict"))
            
        # Parse feature fields from request
        inputs = {}
        try:
            for feature in metadata["feature_cols"]:
                inputs[feature] = request.form.get(feature)
                if inputs[feature] is None:
                    raise ValueError(f"Missing required field: {feature}")
                    
            # Predict
            prediction, meta = ml_engine.predict_crop_area(inputs)
            # Generate suggestions
            suggestions = ml_engine.get_suggestions(prediction, inputs, meta)
            
            # Save prediction record in SQLite db
            database.add_prediction(session["username"], inputs, prediction, suggestions)
            
            # Save results in session to display in result_page
            session["last_prediction"] = {
                "prediction": prediction,
                "inputs": inputs,
                "suggestions": suggestions
            }
            return redirect(url_for("result_page"))
        except Exception as e:
            flash(f"Prediction Error: {str(e)}", "danger")
            return redirect(url_for("predict"))
            
    return render_template("user.html", metadata=metadata)

@app.route("/result")
def result_page():
    if not login_required("user"):
        flash("Please log in to view results.", "danger")
        return redirect(url_for("home"))
        
    last_pred = session.get("last_prediction")
    if not last_pred:
        flash("No active prediction found. Please submit details first.", "danger")
        return redirect(url_for("predict"))
        
    # Read active model metadata
    metadata = None
    metadata_path = os.path.join(ml_engine.MODEL_DIR, "model_metadata.pkl")
    if os.path.exists(metadata_path):
        import pickle
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
            
    return render_template(
        "result.html", 
        prediction=last_pred["prediction"], 
        inputs=last_pred["inputs"], 
        suggestions=last_pred["suggestions"],
        metadata=metadata
    )

@app.route("/history")
def history():
    if not login_required("user"):
        flash("Please log in to access your history.", "danger")
        return redirect(url_for("home"))
        
    predictions = database.get_predictions_for_user(session["username"])
    return render_template("previous_results.html", predictions=predictions)

# --- ADMIN ROUTES ---

@app.route("/admin")
def admin_dashboard():
    if not login_required("admin"):
        flash("Access Denied. Admin privilege required.", "danger")
        return redirect(url_for("home", tab="admin"))
        
    user_count = len(database.get_all_users())
    prediction_count = len(database.get_all_predictions())
    
    # Active model information
    best_model_name = None
    metadata_path = os.path.join(ml_engine.MODEL_DIR, "model_metadata.pkl")
    if os.path.exists(metadata_path):
        import pickle
        with open(metadata_path, "rb") as f:
            meta = pickle.load(f)
            best_model_name = meta.get("best_model_name")
            
    return render_template(
        "admin.html", 
        user_count=user_count, 
        prediction_count=prediction_count, 
        best_model_name=best_model_name
    )

@app.route("/admin/upload", methods=["POST"])
def admin_upload_dataset():
    if not login_required("admin"):
        flash("Access Denied.", "danger")
        return redirect(url_for("home"))
        
    if "file" not in request.files:
        flash("No file part in upload request.", "danger")
        return redirect(url_for("admin_train"))
        
    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("admin_train"))
        
    if file:
        filename = "active_dataset" + os.path.splitext(file.filename)[1]
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        
        # Save filepath in session
        session["uploaded_file_path"] = file_path
        session["uploaded_file_name"] = file.filename
        
        # Clear past training results in session
        session.pop("train_results", None)
        
        flash("Dataset uploaded successfully! Now configure features and train.", "success")
        return redirect(url_for("admin_train"))

@app.route("/admin/train")
def admin_train():
    if not login_required("admin"):
        flash("Access Denied.", "danger")
        return redirect(url_for("home"))
        
    file_path = session.get("uploaded_file_path")
    filename = session.get("uploaded_file_name")
    columns = []
    
    if file_path and os.path.exists(file_path):
        try:
            df = ml_engine.load_dataset(file_path)
            columns = df.columns.tolist()
        except Exception as e:
            flash(f"Error reading uploaded dataset: {e}", "danger")
            session.pop("uploaded_file_path", None)
            session.pop("uploaded_file_name", None)
            
    train_results = session.get("train_results")
    best_model_name = session.get("train_best_model")
    feature_cols = session.get("train_features")
    target_col = session.get("train_target")
    scaler_type = session.get("train_scaler")
    
    return render_template(
        "admin_train.html",
        filename=filename,
        columns=columns,
        train_results=train_results,
        best_model_name=best_model_name,
        feature_cols=feature_cols,
        target_col=target_col,
        scaler_type=scaler_type,
        timestamp=int(time.time()) # query-buster for charts
    )

@app.route("/admin/train_model", methods=["POST"])
def admin_train_model():
    if not login_required("admin"):
        flash("Access Denied.", "danger")
        return redirect(url_for("home"))
        
    file_path = session.get("uploaded_file_path")
    if not file_path or not os.path.exists(file_path):
        flash("No dataset uploaded yet. Please upload a dataset first.", "danger")
        return redirect(url_for("admin_train"))
        
    feature_cols = request.form.getlist("feature_cols")
    target_col = request.form.get("target_col")
    scaler_type = request.form.get("scaler_type", "standard")
    
    if not feature_cols:
        flash("Please select at least one feature column (X).", "danger")
        return redirect(url_for("admin_train"))
        
    if target_col in feature_cols:
        flash("Target column (Y) cannot be part of feature columns (X).", "danger")
        return redirect(url_for("admin_train"))
        
    try:
        # Load and preprocess
        df = ml_engine.load_dataset(file_path)
        cleaned_df = ml_engine.preprocess_data(df)
        
        # Generate the 6 data visualizations
        ml_engine.generate_visualizations(cleaned_df, target_col)
        
        # Train and save the best model
        results, best_model_name = ml_engine.train_and_save_model(
            cleaned_df, feature_cols, target_col, scaler_type
        )
        
        # Save training outcomes in session
        session["train_results"] = results
        session["train_best_model"] = best_model_name
        session["train_features"] = feature_cols
        session["train_target"] = target_col
        session["train_scaler"] = scaler_type
        
        flash("Machine learning models trained successfully!", "success")
    except Exception as e:
        flash(f"Training Failed: {str(e)}", "danger")
        
    return redirect(url_for("admin_train"))

@app.route("/admin/users")
def admin_users():
    if not login_required("admin"):
        flash("Access Denied.", "danger")
        return redirect(url_for("home"))
        
    users = database.get_all_users()
    return render_template("admin_users.html", users=users)

@app.route("/admin/results")
def admin_results():
    if not login_required("admin"):
        flash("Access Denied.", "danger")
        return redirect(url_for("home"))
        
    predictions = database.get_all_predictions()
    return render_template("admin_results.html", predictions=predictions)

if __name__ == "__main__":
    app.run(debug=True)
