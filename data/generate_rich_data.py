import os
import csv
import random

def main():
    # Mapping of states and districts that are supported in the dataset
    states_districts = {
        "Maharashtra": ["Pune", "Nashik", "Nagpur", "Satara", "Solapur", "Aurangabad", "Kolhapur"],
        "Karnataka": ["Belagavi", "Tumakuru", "Mysuru", "Dharwad", "Mandya", "Bengaluru Rural", "Bidar"],
        "Uttar Pradesh": ["Meerut", "Varanasi", "Kanpur", "Bareilly", "Gorakhpur", "Agra", "Aligarh", "Allahabad"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Ferozepur", "Gurdaspur"],
        "Tamil Nadu": ["Coimbatore", "Thanjavur", "Madurai", "Salem", "Tiruchirappalli", "Erode", "Vellore"],
        "Andhra Pradesh": ["Guntur", "Krishna", "Kurnool", "Visakhapatnam", "Chittoor", "Anantapur"],
        "West Bengal": ["Burdwan", "Murshidabad", "Nadia", "Birbhum", "Hooghly", "Midnapore"],
        "Gujarat": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Jamnagar", "Bhavnagar"],
        "Madhya Pradesh": ["Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain", "Sagar"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer"]
    }
    
    seasons = ["Kharif", "Rabi", "Summer", "Whole Year"]
    
    # 20 different crops with realistic yield parameters (yield range in tonnes per hectare) and seasons
    crop_yield_factors = {
        # Cereals
        "Rice": {"yield_range": (2.0, 4.5), "seasons": ["Kharif", "Summer"]},
        "Wheat": {"yield_range": (2.5, 4.8), "seasons": ["Rabi"]},
        "Maize": {"yield_range": (2.5, 5.0), "seasons": ["Kharif", "Rabi", "Summer"]},
        "Barley": {"yield_range": (1.8, 3.2), "seasons": ["Rabi"]},
        "Bajra": {"yield_range": (1.0, 2.2), "seasons": ["Kharif", "Summer"]},
        "Jowar": {"yield_range": (0.8, 1.8), "seasons": ["Kharif", "Rabi"]},
        "Ragi": {"yield_range": (1.2, 2.5), "seasons": ["Kharif", "Rabi"]},
        
        # Pulses & Oilseeds
        "Gram": {"yield_range": (0.9, 1.6), "seasons": ["Rabi"]},
        "Soybean": {"yield_range": (1.1, 2.3), "seasons": ["Kharif"]},
        "Groundnut": {"yield_range": (1.4, 2.8), "seasons": ["Kharif", "Rabi", "Summer"]},
        "Mustard": {"yield_range": (1.0, 1.9), "seasons": ["Rabi"]},
        
        # Cash Crops
        "Cotton": {"yield_range": (1.5, 3.0), "seasons": ["Kharif"]},
        "Sugarcane": {"yield_range": (65.0, 105.0), "seasons": ["Whole Year"]},
        "Coconut": {"yield_range": (8.0, 15.0), "seasons": ["Whole Year"]},
        "Tobacco": {"yield_range": (1.2, 2.4), "seasons": ["Rabi"]},
        
        # Vegetables & Spices
        "Potato": {"yield_range": (18.0, 28.0), "seasons": ["Rabi", "Winter"]},
        "Tomato": {"yield_range": (15.0, 25.0), "seasons": ["Summer", "Kharif", "Rabi"]},
        "Onion": {"yield_range": (14.0, 22.0), "seasons": ["Rabi", "Kharif", "Summer"]},
        "Turmeric": {"yield_range": (4.0, 6.5), "seasons": ["Whole Year"]},
        "Ginger": {"yield_range": (3.5, 5.8), "seasons": ["Whole Year"]}
    }

    out_dir = r"e:\AI-Powered-Crop-Yield-Prediction-and-Optimization\data"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "crop_yield.csv")
    
    headers = ["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production"]
    
    random.seed(100)
    rows = []
    
    # Generate 1500 records
    for _ in range(1500):
        state = random.choice(list(states_districts.keys()))
        district = random.choice(states_districts[state])
        year = random.randint(2015, 2026)
        crop = random.choice(list(crop_yield_factors.keys()))
        
        crop_info = crop_yield_factors[crop]
        season = random.choice(crop_info["seasons"])
        
        # Area in hectares
        area = round(random.uniform(50, 150000), 2)
        
        # Production in tonnes
        yield_multiplier = random.uniform(*crop_info["yield_range"])
        production = round(area * yield_multiplier, 2)
        
        # Add details
        rows.append([state, district, year, season, crop, area, production])
        
    # Introduce some duplicates for the training pre-process stage
    for i in range(25):
        dup_row = list(random.choice(rows))
        rows.append(dup_row)
        
    # Introduce some null values for Area or Production
    for _ in range(35):
        null_row_idx = random.randint(0, len(rows) - 1)
        col_to_null = random.choice([5, 6])
        rows[null_row_idx][col_to_null] = ""
        
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        
    print(f"Generated {len(rows)} rich crop yield records in {out_file}")

if __name__ == "__main__":
    main()
