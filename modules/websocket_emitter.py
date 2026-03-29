# WebSocket Event Emitter
# Provides a singleton to emit real-time events to connected clients

class WebSocketEmitter:
    """Singleton class to emit WebSocket events from anywhere in the app"""
    
    def __init__(self):
        self._socketio = None
        self._connected = False
    
    def init_app(self, socketio):
        """Initialize with Flask-SocketIO instance"""
        self._socketio = socketio
        self._connected = True
        print("[WS] WebSocket emitter initialized")
    
    def emit_stats(self, data):
        """Emit dashboard stats update"""
        if self._socketio and self._connected:
            self._socketio.emit('stats_update', data)
    
    def emit_price_change(self, data):
        """Emit new price change"""
        if self._socketio and self._connected:
            self._socketio.emit('price_change', data)
    
    def emit_price_chart(self, data):
        """Emit price chart data"""
        if self._socketio and self._connected:
            self._socketio.emit('price_chart_update', data)
    
    def emit_demand_chart(self, data):
        """Emit demand chart data"""
        if self._socketio and self._connected:
            self._socketio.emit('demand_chart_update', data)
    
    def emit_recent_changes(self, data):
        """Emit recent price changes"""
        if self._socketio and self._connected:
            self._socketio.emit('recent_changes_update', data)
    
    def emit_simulation_tick(self, data):
        """Emit simulation tick event"""
        if self._socketio and self._connected:
            self._socketio.emit('simulation_tick', data)
    
    def emit_homepage_update(self, data):
        """Emit homepage-specific product updates"""
        if self._socketio and self._connected:
            self._socketio.emit('homepage_update', data)
    
    def emit_restock(self, data):
        """Emit restock event when products are replenished"""
        if self._socketio and self._connected:
            self._socketio.emit('restock', data)
    
    def emit_product_update(self, data):
        """Emit product update (for admin edits)"""
        if self._socketio and self._connected:
            self._socketio.emit('product_update', data)
    
    def emit_all(self):
        """Emit all dashboard data (full refresh)"""
        if self._socketio and self._connected:
            self._socketio.emit('full_refresh')


# Global singleton instance
ws_emitter = WebSocketEmitter()
