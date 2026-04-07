import random
import time
import threading

from app.extensions import db   # ← MUST be from extensions
from app.config import Config
from app.models import SimulatedUser, UserType, Product, UserAction
from utils.datetime_utils import get_utc_now

# Import WebSocket emitter (optional - graceful fallback)
try:
    from modules.websocket_emitter import ws_emitter
except ImportError:
    ws_emitter = None

class SimulationEngine:
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None
        self.tick_rate = Config.SIMULATION_TICK_RATE

    def start(self, flask_app):
        if self.running:
            return
        self.app = flask_app
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[SIM] Simulation started - {Config.NUM_SIMULATED_USERS} users every {self.tick_rate}s")

    def _run_loop(self):
        print("[SIM] Simulation thread started - waiting for context...")
        while self.running:
            try:
                with self.app.app_context():   # ← FULL CONTEXT EVERY TICK
                    self._simulate_one_tick()
            except Exception as e:
                print(f"[SIM] Tick error: {e}")
            time.sleep(self.tick_rate)

    def _simulate_one_tick(self):
        sim_users = SimulatedUser.query.all()
        all_products = Product.query.filter(Product.stock > 0).all()
        if not all_products:
            return

        # IMPERFECT SIMULATOR: Only give attention to a subset of products
        # This lets some products naturally "cool down" between attention
        activity_rate = Config.SIMULATOR_ACTIVITY_RATE
        num_active = max(1, int(len(all_products) * activity_rate))
        # Ensure k <= population to avoid ValueError from random.sample
        k = min(num_active, len(all_products))
        products = random.sample(all_products, k=k)
        
        # Only 20% of users act per tick - keeps activity realistic
        users_this_tick = random.sample(sim_users, k=max(1, int(len(sim_users) * 0.2)))
        
        actions_this_tick = 0

        for sim_user in users_this_tick:
            user_type = UserType.query.get(sim_user.type_id)
            if not user_type:
                continue

            # Random product selection for realistic simulation behavior
            # Each user type has different preferences, so random selection models this
            product = random.choice(products)
            price_ratio = product.current_price / product.base_price
            stock_ratio = product.stock / 100.0

            personality = user_type.type_name.lower()
            view_p = user_type.view_probability
            cart_p = user_type.cart_probability
            purchase_p = user_type.purchase_probability

            # Personality modifiers
            if personality == "optimist":
                if price_ratio > 1.05 or stock_ratio < 0.3:
                    purchase_p *= 1.8
                cart_p *= 1.3
            elif personality == "pessimist":
                if price_ratio > 1.1:
                    purchase_p *= 0.3
                    cart_p *= 0.5
                elif price_ratio < 0.95:
                    purchase_p *= 1.6
            elif personality == "envious":
                if stock_ratio < 0.4:
                    purchase_p *= 1.7
                    cart_p *= 1.4
            elif personality == "bargain hunter":
                if price_ratio > 1.08:
                    purchase_p = 0.0
                    cart_p *= 0.2
                elif price_ratio < 0.97:
                    purchase_p *= 2.0
            elif personality == "impulse buyer":
                if stock_ratio < 0.25 or random.random() < 0.4:
                    purchase_p *= 2.5
                cart_p *= 1.6

            r = random.random()
            if r < view_p:
                self._log_action(sim_user.sim_user_id, product.product_id, 'view')
                actions_this_tick += 1

                if random.random() < cart_p:
                    self._log_action(sim_user.sim_user_id, product.product_id, 'cart')
                    actions_this_tick += 1

                    if random.random() < purchase_p and product.stock > 0:
                        self._log_action(sim_user.sim_user_id, product.product_id, 'purchase')
                        actions_this_tick += 1
                        product.stock -= 1
                        # Note: Restock is now handled by pricing engine, not simulation

        db.session.commit()

        if actions_this_tick > 0:
            print(f"[SIM] Tick done - {actions_this_tick} actions on {len(products)}/{len(all_products)} products | System breathing!")
            
            # Emit WebSocket event if available
            if ws_emitter:
                ws_emitter.emit_simulation_tick({
                    'actions': actions_this_tick,
                    'timestamp': get_utc_now().isoformat()
                })

    def _log_action(self, sim_user_id, product_id, action_type):
        action = UserAction(
            sim_user_id=sim_user_id,
            product_id=product_id,
            action_type=action_type,
            timestamp=get_utc_now()
        )
        db.session.add(action)


simulation = SimulationEngine()