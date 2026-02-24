# File: backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
# Allow all origins, which is fine for Vercel deployment
CORS(app, resources={r"/api/*": {"origins": "*"}}) 

data_file_name = 'Zomato_Menu_Classified_with_Area.csv'

try:
    script_dir = os.path.dirname(__file__) 
    file_path = os.path.join(script_dir, data_file_name)
    
    print(f"--- LOG: Attempting to load data from: {file_path}")
    df = pd.read_csv(file_path)
    print(f"--- LOG: CSV file loaded. Initial row count: {len(df)}")
    print(f"--- LOG: Columns found: {df.columns.tolist()}")

    # --- ADVANCED PRICE CLEANING ---
    if 'Price' in df.columns:
        print("--- LOG: Starting 'Price' column cleaning...")
        # First, drop rows where 'Price' is already empty
        df.dropna(subset=['Price'], inplace=True)
        print(f"--- LOG: Rows after dropping empty prices: {len(df)}")
        
        # Convert to string and use regex to remove everything that isn't a digit or decimal
        df['Price'] = df['Price'].astype(str).str.replace(r'[^\d.]', '', regex=True)
        
        # After cleaning, some might be empty strings. Replace them with NaN.
        df.loc[df['Price'] == '', 'Price'] = pd.NA
        print(f"--- LOG: Rows after replacing empty strings in Price: {len(df)}")

        # Now convert to numeric. Coerce will handle any remaining bad formats.
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        # Finally, drop any rows that could not be converted.
        df.dropna(subset=['Price'], inplace=True)
        print(f"--- LOG: Rows after final numeric conversion of Price: {len(df)}")
    else:
        print("--- LOG: WARNING - 'Price' column not found.")

    # --- CLEAN OTHER CRITICAL COLUMNS ---
    # This is another potential point of failure. We will check it too.
    initial_rows_before_final_clean = len(df)
    df.dropna(subset=['Item_Name', 'Restaurant_Name', 'Food Type', 'Cuisine'], inplace=True)
    print(f"--- LOG: Rows after cleaning other critical columns: {len(df)}")
    print(f"--- LOG: Dropped {initial_rows_before_final_clean - len(df)} rows due to missing critical data.")
    
    print(f"--- LOG: FINAL DATA READY with {len(df)} rows.")
        
except Exception as e:
    print(f"--- LOG: FATAL ERROR - An exception occurred during data loading: {e}")
    df = pd.DataFrame() # Ensure df is empty on error

# --- API Endpoint (no changes needed here) ---
@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    if df.empty:
        return jsonify({"error": "Server data is empty or not loaded correctly."}), 500
    
    # ... rest of the function is the same ...
    data = request.get_json()
    food_types = data.get('foodTypes', [])
    cuisines = data.get('cuisines', [])
    min_price = data.get('minPrice')
    max_price = data.get('maxPrice')
    filtered_df = df.copy()
    if food_types: filtered_df = filtered_df[filtered_df['Food Type'].isin(food_types)]
    if cuisines: filtered_df = filtered_df[filtered_df['Cuisine'].isin(cuisines)]
    if 'Price' in filtered_df.columns:
        if min_price is not None: filtered_df = filtered_df[filtered_df['Price'] >= float(min_price)]
        if max_price is not None: filtered_df = filtered_df[filtered_df['Price'] <= float(max_price)]
    if filtered_df.empty: return jsonify([])
    num_samples = min(len(filtered_df), 5)
    recommendations = filtered_df.sample(n=num_samples)
    return jsonify(recommendations.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=False, port=5000)