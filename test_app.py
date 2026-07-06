import os
import unittest
import json
import sqlite3
from app import app, ADMIN_USERNAME, ADMIN_PASSWORD
import database
import ml_engine

class CropAppTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        
        # We will use the default files, but we can verify their creation
        database.init_dbs()
        
    def test_1_homepage_status(self):
        """Test that the homepage loaded successfully."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CropPrediction", response.data)

    def test_2_default_model_seeded(self):
        """Test that the default model and visualizations were seeded."""
        best_model_path = os.path.join(ml_engine.MODEL_DIR, "best_model.pkl")
        metadata_path = os.path.join(ml_engine.MODEL_DIR, "model_metadata.pkl")
        
        self.assertTrue(os.path.exists(best_model_path), "best_model.pkl does not exist")
        self.assertTrue(os.path.exists(metadata_path), "model_metadata.pkl does not exist")
        
        # Verify visualizations
        for plot_name in ["plot_target_dist.png", "plot_correlation.png", "plot_by_season.png", 
                          "plot_by_state.png", "plot_over_time.png", "plot_distribution_boxplot.png"]:
            plot_path = os.path.join(ml_engine.VIS_DIR, plot_name)
            self.assertTrue(os.path.exists(plot_path), f"{plot_name} does not exist")

    def test_3_signup_validation_failures(self):
        """Test that invalid signup entries are rejected (ends in gmail, phone validation, etc)."""
        # Test invalid email (not ending in @gmail.com)
        response = self.client.post("/signup", data={
            "name": "Test User",
            "username": "testuser_fail1",
            "email": "test@yahoo.com",
            "phone": "+919876543210",
            "password": "Amma@1234",
            "confirm_password": "Amma@1234"
        }, follow_redirects=True)
        self.assertIn(b"Email must end with @gmail.com", response.data)
        
        # Test invalid phone (not starting with +91)
        response = self.client.post("/signup", data={
            "name": "Test User",
            "username": "testuser_fail2",
            "email": "test@gmail.com",
            "phone": "9876543210",
            "password": "Amma@1234",
            "confirm_password": "Amma@1234"
        }, follow_redirects=True)
        self.assertIn(b"Phone number must be +91 followed by 10 digits", response.data)
        
        # Test invalid password (no uppercase)
        response = self.client.post("/signup", data={
            "name": "Test User",
            "username": "testuser_fail3",
            "email": "test@gmail.com",
            "phone": "+919876543210",
            "password": "amma@1234",
            "confirm_password": "amma@1234"
        }, follow_redirects=True)
        self.assertIn(b"Password does not meet complexity requirements", response.data)

    def test_4_signup_success_and_login(self):
        """Test a successful signup and subsequent user login."""
        # Create a unique test user
        username = "test_farmer_99"
        email = "farmer99@gmail.com"
        
        # Direct DB cleanup to ensure test repeatability
        conn = sqlite3.connect(database.SIGNUP_DB)
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        
        # Signup request
        response = self.client.post("/signup", data={
            "name": "Farmer Ninety-Nine",
            "username": username,
            "email": email,
            "phone": "+919998887776",
            "password": "Amma@1234",
            "confirm_password": "Amma@1234"
        }, follow_redirects=True)
        self.assertIn(b"Account created successfully! Please sign in", response.data)
        
        # Attempt Login (Success)
        response = self.client.post("/login/user", data={
            "username": username,
            "email": email,
            "password": "Amma@1234"
        }, follow_redirects=True)
        self.assertIn(b"Welcome back", response.data)
        
        # Attempt Login (Failure - bad password)
        response = self.client.post("/login/user", data={
            "username": username,
            "email": email,
            "password": "WrongPassword@123"
        }, follow_redirects=True)
        self.assertIn(b"Invalid username", response.data)

    def test_5_admin_login(self):
        """Test admin authentication."""
        # Success
        response = self.client.post("/login/admin", data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }, follow_redirects=True)
        self.assertIn(b"Admin Hub", response.data)
        
        # Failure
        response = self.client.post("/login/admin", data={
            "username": ADMIN_USERNAME,
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertIn(b"Invalid Admin credentials", response.data)

    def test_6_predictions(self):
        """Test prediction calculations and storage."""
        # Input matching seeded crop_yield features:
        # ["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Production"]
        sample_input = {
            "State_Name": "Maharashtra",
            "District_Name": "Pune",
            "Crop_Year": 2020,
            "Season": "Kharif",
            "Crop": "Rice",
            "Production": 15000.0
        }
        
        prediction, meta = ml_engine.predict_crop_area(sample_input)
        self.assertIsInstance(prediction, float)
        self.assertGreater(prediction, 0)
        
        suggestions = ml_engine.get_suggestions(prediction, sample_input, meta)
        self.assertIn("area occupied", suggestions.lower())
        
        # Test adding prediction record
        database.add_prediction("test_farmer_99", sample_input, prediction, suggestions)
        history = database.get_predictions_for_user("test_farmer_99")
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["prediction"], prediction)

if __name__ == "__main__":
    unittest.main()
