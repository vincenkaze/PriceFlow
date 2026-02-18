# run.py
from app import create_app
import os


# Create app with default (development) config
app = create_app()

if __name__ == '__main__':
    # Optional: create instance folder if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    print(" Starting Intelligent Dynamic Pricing System...")
    print("   Simulation ready • 200 fake users • Prices will move like crazy")
    print("   Visit → http://127.0.0.1:5000")
    
    # Run with debug + auto-reload (perfect for our chaotic dev life)
    app.run(host='0.0.0.0', port=5000, debug=True)