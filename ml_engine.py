import os
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, accuracy_score

MODEL_DIR = os.path.join("static", "models")
VIS_DIR = os.path.join("static", "visualizations")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(VIS_DIR, exist_ok=True)

def load_dataset(file_path):
    """Loads CSV or Excel datasets."""
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.csv':
        return pd.read_csv(file_path)
    elif ext.lower() in ['.xls', '.xlsx']:
        return pd.read_excel(file_path)
    elif ext.lower() == '.txt':
        # Guess delimiter: tab or comma
        with open(file_path, 'r') as f:
            first_line = f.readline()
        if '\t' in first_line:
            return pd.read_csv(file_path, sep='\t')
        else:
            return pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV, Excel, or txt files.")

def preprocess_data(df):
    """Cleans dataset: drops duplicates, fills null values."""
    # Drop duplicates
    cleaned_df = df.drop_duplicates()
    
    # Fill nulls
    for col in cleaned_df.columns:
        if cleaned_df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                # Fill numeric with median
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
            else:
                # Fill categorical with mode
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0])
    return cleaned_df

def generate_visualizations(df, target_col):
    """Generates 6 distinct plots and saves them as PNG files in static/visualizations/."""
    # Reset styling and figure
    plt.clf()
    sns.set_theme(style="darkgrid")
    
    # 1. Distribution of Target Column
    plt.figure(figsize=(8, 5))
    if pd.api.types.is_numeric_dtype(df[target_col]):
        sns.histplot(df[target_col], kde=True, color="#00F0FF")
    else:
        sns.countplot(x=target_col, data=df, palette="viridis")
        plt.xticks(rotation=45)
    plt.title(f"Distribution of Target: {target_col}", fontsize=14, fontweight='bold', color="#101415")
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "plot_target_dist.png"))
    plt.close()

    # 2. Correlation Heatmap for Numerical Columns
    plt.figure(figsize=(8, 5))
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] > 1:
        corr = num_df.corr()
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    else:
        # Dummy plot if not enough numerical columns
        plt.text(0.5, 0.5, "Not enough numerical features\nfor correlation heatmap", 
                 ha='center', va='center', fontsize=12)
    plt.title("Correlation Heatmap of Numerical Features", fontsize=14, fontweight='bold', color="#101415")
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "plot_correlation.png"))
    plt.close()

    # 3. Target by Season (if 'Season' is present, otherwise random categorical)
    plt.figure(figsize=(8, 5))
    cat_cols = df.select_dtypes(exclude=[np.number]).columns
    season_like_col = next((c for c in cat_cols if 'season' in c.lower()), None)
    if not season_like_col and len(cat_cols) > 0:
        season_like_col = cat_cols[0]
        
    if season_like_col and pd.api.types.is_numeric_dtype(df[target_col]):
        sns.barplot(x=season_like_col, y=target_col, data=df, errorbar=None, palette="magma")
        plt.xticks(rotation=30)
        plt.title(f"Average {target_col} by {season_like_col}", fontsize=14, fontweight='bold', color="#101415")
    else:
        plt.text(0.5, 0.5, "No suitable categorical feature\nfor target grouping", 
                 ha='center', va='center', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "plot_by_season.png"))
    plt.close()

    # 4. Target by State (if 'State_Name' or similar present, otherwise another categorical)
    plt.figure(figsize=(8, 5))
    state_like_col = next((c for c in cat_cols if 'state' in c.lower()), None)
    if not state_like_col and len(cat_cols) > 1:
        state_like_col = cat_cols[1]
    elif not state_like_col and len(cat_cols) > 0:
        state_like_col = cat_cols[0]

    if state_like_col and pd.api.types.is_numeric_dtype(df[target_col]):
        # Top 10 categories if too many
        top_cats = df[state_like_col].value_counts().nlargest(10).index
        filtered_df = df[df[state_like_col].isin(top_cats)]
        sns.barplot(x=state_like_col, y=target_col, data=filtered_df, errorbar=None, palette="viridis")
        plt.xticks(rotation=45)
        plt.title(f"Average {target_col} by Top {state_like_col}", fontsize=14, fontweight='bold', color="#101415")
    else:
        plt.text(0.5, 0.5, "No suitable categorical feature\nfor state-wise target breakdown", 
                 ha='center', va='center', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "plot_by_state.png"))
    plt.close()

    # 5. Target over Years (if 'Crop_Year' or 'Year' or similar is present)
    plt.figure(figsize=(8, 5))
    year_like_col = next((c for c in num_df.columns if 'year' in c.lower() or 'date' in c.lower()), None)
    if year_like_col and pd.api.types.is_numeric_dtype(df[target_col]):
        sns.lineplot(x=year_like_col, y=target_col, data=df, errorbar=None, marker='o', color="#9D4EDD")
        plt.title(f"Trend of {target_col} over {year_like_col}", fontsize=14, fontweight='bold', color="#101415")
    else:
        plt.text(0.5, 0.5, "No temporal feature (Year)\nfound in dataset", 
                 ha='center', va='center', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "plot_over_time.png"))
    plt.close()

    # 6. Target Boxplot per Crop (if 'Crop' or similar is present)
    plt.figure(figsize=(8, 5))
    crop_like_col = next((c for c in cat_cols if 'crop' in c.lower() or 'type' in c.lower()), None)
    if not crop_like_col and len(cat_cols) > 0:
        crop_like_col = cat_cols[-1]

    if crop_like_col and pd.api.types.is_numeric_dtype(df[target_col]):
        top_crops = df[crop_like_col].value_counts().nlargest(8).index
        filtered_df = df[df[crop_like_col].isin(top_crops)]
        sns.boxplot(x=crop_like_col, y=target_col, data=filtered_df, palette="plasma")
        plt.xticks(rotation=45)
        plt.title(f"{target_col} Distribution for Top {crop_like_col}s", fontsize=14, fontweight='bold', color="#101415")
    else:
        plt.text(0.5, 0.5, "No suitable column for\nboxplot category distribution", 
                 ha='center', va='center', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "plot_distribution_boxplot.png"))
    plt.close()

def train_and_save_model(df, feature_cols, target_col, scaler_type='standard'):
    """Trains 3 ML algorithms, selects the best model, and saves it."""
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    is_classification = not pd.api.types.is_numeric_dtype(y)
    
    # Store encoder instances, scaler instance, and categorical classes
    label_encoders = {}
    scaler = None
    
    # Encode categorical features in X
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
            
    # Encode target if it is classification
    target_encoder = None
    if is_classification:
        target_encoder = LabelEncoder()
        y = target_encoder.fit_transform(y.astype(str))
        
    # Standardize or normalize numerical features in X
    num_features = X.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude encoded columns from scaling if desired, but standard is scaling numericals
    # Note: Encodings are now integers, let's only scale original numerical columns
    orig_num_features = [col for col in num_features if col not in label_encoders]
    
    if len(orig_num_features) > 0:
        if scaler_type == 'standard':
            scaler = StandardScaler()
            X[orig_num_features] = scaler.fit_transform(X[orig_num_features])
        elif scaler_type == 'minmax':
            scaler = MinMaxScaler()
            X[orig_num_features] = scaler.fit_transform(X[orig_num_features])
            
    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    results = {}
    trained_models = {}
    
    if is_classification:
        # Classifier Models
        models = {
            "Random Forest Classifier": RandomForestClassifier(n_estimators=100, random_state=42),
            "Decision Tree Classifier": DecisionTreeClassifier(random_state=42),
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42)
        }
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            results[name] = {"metric_name": "Accuracy", "score": float(acc), "mae": None, "mse": None}
            trained_models[name] = model
            
        # Select best model based on Accuracy
        best_model_name = max(results, key=lambda k: results[k]["score"])
    else:
        # Regressor Models
        models = {
            "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
            "Decision Tree Regressor": DecisionTreeRegressor(random_state=42),
            "Linear Regression": LinearRegression()
        }
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            results[name] = {"metric_name": "R2 Score", "score": float(r2), "mae": float(mae), "mse": float(mse)}
            trained_models[name] = model
            
        # Select best model based on R2 Score
        best_model_name = max(results, key=lambda k: results[k]["score"])
        
    best_model = trained_models[best_model_name]
    
    # Save the best model and metadata
    metadata = {
        "feature_cols": feature_cols,
        "target_col": target_col,
        "is_classification": is_classification,
        "label_encoders": label_encoders,
        "target_encoder": target_encoder,
        "scaler": scaler,
        "scaler_type": scaler_type,
        "orig_num_features": orig_num_features,
        "best_model_name": best_model_name,
        "results": results,
        # Save sample data values to populate dropdowns on frontend
        "feature_choices": {
            col: (label_encoders[col].classes_.tolist() if col in label_encoders else None)
            for col in feature_cols
        }
    }
    
    best_model_path = os.path.join(MODEL_DIR, "best_model.pkl")
    metadata_path = os.path.join(MODEL_DIR, "model_metadata.pkl")
    
    with open(best_model_path, "wb") as f:
        pickle.dump(best_model, f)
        
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)
        
    return results, best_model_name

def predict_crop_area(input_dict):
    """Loads active model, pre-processes the input dictionary, and predicts."""
    best_model_path = os.path.join(MODEL_DIR, "best_model.pkl")
    metadata_path = os.path.join(MODEL_DIR, "model_metadata.pkl")
    
    if not os.path.exists(best_model_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError("No trained model exists. Train a model in the admin page first.")
        
    with open(best_model_path, "rb") as f:
        model = pickle.load(f)
        
    with open(metadata_path, "rb") as f:
        meta = pickle.load(f)
        
    feature_cols = meta["feature_cols"]
    label_encoders = meta["label_encoders"]
    scaler = meta["scaler"]
    orig_num_features = meta["orig_num_features"]
    is_classification = meta["is_classification"]
    target_encoder = meta["target_encoder"]
    
    # Create input DataFrame matching feature columns
    input_df = pd.DataFrame([input_dict])
    input_df = input_df.astype(object)
    
    # Process categorical encoders
    for col in feature_cols:
        if col in label_encoders:
            le = label_encoders[col]
            val = str(input_df.loc[0, col])
            # If value not in classes, map to the most common or first class to prevent error
            if val not in le.classes_:
                input_df.loc[0, col] = le.transform([le.classes_[0]])[0]
            else:
                input_df.loc[0, col] = le.transform([val])[0]
        else:
            # Numeric conversion
            input_df.loc[0, col] = pd.to_numeric(input_df.loc[0, col])
            
    # Apply scaler if it exists
    if scaler and len(orig_num_features) > 0:
        input_df[orig_num_features] = scaler.transform(input_df[orig_num_features])
        
    # Reorder columns to match training order
    input_df = input_df[feature_cols]
    
    # Predict
    pred = model.predict(input_df)[0]
    
    if is_classification and target_encoder:
        prediction_result = target_encoder.inverse_transform([pred])[0]
    else:
        prediction_result = float(pred)
        
    return prediction_result, meta

def get_suggestions(prediction, inputs, meta):
    """Generates user recommendations based on inputs and predictions."""
    suggestions = []
    
    crop = inputs.get("Crop", "the selected crop")
    state = inputs.get("State_Name", "your region")
    season = inputs.get("Season", "the season")
    
    is_classification = meta.get("is_classification", False)
    
    if is_classification:
        suggestions.append(f"Based on historical data for {state} in {season}, planting {crop} is predicted to yield a category of '{prediction}'.")
        suggestions.append("Apply local organic manure and test soil pH to optimize nutrients.")
    else:
        area = prediction
        suggestions.append(f"Predicted area occupied for {crop} under these conditions is {area:,.2f} hectares.")
        
        if area > 50000:
            suggestions.append("Given the large cultivation area, consider high levels of mechanization (tractor-mounted seeders, harvesters) to reduce labor overheads.")
            suggestions.append("Implement automated drip/sprinkler irrigation systems with soil moisture telemetry to minimize water waste across extensive tracts.")
            suggestions.append("Adopt regional crop rotation policies (e.g., following with legumes) to preserve nitrogen balance in large fields.")
        elif area > 10000:
            suggestions.append("For medium-sized plots, focus on precision fertilizer application based on targeted soil grid sampling.")
            suggestions.append("Incorporate mulching techniques to optimize moisture retention and suppress weeds in critical zones.")
            suggestions.append("Arrange tie-ups with local agricultural cooperatives for shared transport and processing infrastructure.")
        else:
            suggestions.append("For smaller plots, optimize spacing through high-density planting techniques to maximize yield per square meter.")
            suggestions.append("Focus on micro-irrigation systems (drip tapes) which are highly cost-efficient and controllable on smaller plots.")
            suggestions.append("Use bio-fertilizers and kitchen-waste compost to reduce input costs and build up organic soil matter.")
            
    suggestions.append("Always inspect regional weather reports before finalizing seed sowing dates to mitigate early monsoonal failures or drought spans.")
    return " | ".join(suggestions)
