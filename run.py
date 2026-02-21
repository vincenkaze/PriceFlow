from app import create_app
from modules.user_simulation import simulation
from modules.pricing_engine import pricing_engine
import os

app = create_app()

if __name__ == '__main__':
    os.makedirs('instance', exist_ok=True)

    print("\n Starting Intelligent Dynamic Pricing System...")
    print("   200 Optimists, Pessimists, Bargain Hunters & Impulse Buyers are now feral")
    print("   Visit → http://127.0.0.1:5000")

    # Start simulation safely
    with app.app_context():
        simulation.start(app)
        pricing_engine.start(app)

    # CRITICAL: disable reloader
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )