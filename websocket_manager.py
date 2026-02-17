"""
WebSocket Manager for Real-Time Updates
Broadcasts events to connected clients.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
import json
from datetime import datetime, timezone


from collections import defaultdict

class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self, max_connections_per_ip: int = 5):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}
        self.ip_connections: Dict[str, int] = {}
        self.max_connections_per_ip = max_connections_per_ip
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Accept new WebSocket connection."""
        ip = websocket.client.host if websocket.client else "unknown"
        
        if self.ip_connections.get(ip, 0) >= self.max_connections_per_ip:
            await websocket.accept()
            await self.send_personal_message({
                "type": "error",
                "message": f"Connection limit reached for your IP ({self.max_connections_per_ip}). Please close existing sessions."
            }, websocket)
            await websocket.close(code=1008)  # Policy Violation
            return False

        await websocket.accept()
        self.active_connections.append(websocket)
        self.ip_connections[ip] = self.ip_connections.get(ip, 0) + 1
        self.connection_info[websocket] = {
            "client_id": client_id,
            "ip": ip,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "message": "Connected to Vesta real-time updates",
            "client_id": client_id
        }, websocket)
        return True
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            info = self.connection_info.get(websocket)
            if info:
                ip = info.get("ip")
                if ip and ip in self.ip_connections:
                    self.ip_connections[ip] = max(0, self.ip_connections[ip] - 1)
                    if self.ip_connections[ip] <= 0:
                        self.ip_connections.pop(ip, None)
                if websocket in self.connection_info:
                    self.connection_info.pop(websocket, None)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_entity_arrival(self, entity_name: str, location: str):
        """Broadcast entity arrival event."""
        await self.broadcast({
            "type": "entity_arrival",
            "entity_name": entity_name,
            "location": location,
            "message": f"{entity_name} arrived at {location}"
        })
    
    async def broadcast_breeding_started(self, parent_a: str, parent_b: str):
        """Broadcast breeding event."""
        await self.broadcast({
            "type": "breeding_started",
            "parent_a": parent_a,
            "parent_b": parent_b,
            "message": f"Breeding: {parent_a} + {parent_b}"
        })
    
    async def broadcast_breeding_completed(self, offspring_name: str, generation: int):
        """Broadcast offspring birth."""
        await self.broadcast({
            "type": "breeding_completed",
            "offspring": offspring_name,
            "generation": generation,
            "message": f"🎉 {offspring_name} born (Gen {generation})"
        })
    
    async def broadcast_experiment_created(self, creator: str, experiment_name: str):
        """Broadcast new experiment."""
        await self.broadcast({
            "type": "experiment_created",
            "creator": creator,
            "experiment_name": experiment_name,
            "message": f"✨ {creator} created '{experiment_name}'"
        })
    
    async def broadcast_experiment_rated(self, experiment_name: str, stars: int):
        """Broadcast experiment rating."""
        await self.broadcast({
            "type": "experiment_rated",
            "experiment": experiment_name,
            "stars": stars,
            "message": f"⭐ '{experiment_name}' rated {stars} stars"
        })
    
    async def broadcast_badge_unlocked(self, entity_name: str, badge_name: str):
        """Broadcast badge achievement."""
        await self.broadcast({
            "type": "badge_unlocked",
            "entity": entity_name,
            "badge": badge_name,
            "message": f"🏆 {entity_name} unlocked '{badge_name}'"
        })
    
    async def broadcast_quarantine(self, entity_name: str, reason: str):
        """Broadcast quarantine event."""
        await self.broadcast({
            "type": "quarantine",
            "entity": entity_name,
            "reason": reason,
            "message": f"🚨 {entity_name} quarantined: {reason}"
        })
    
    async def broadcast_soul_swap(self, entity_name: str, tincture: str):
        """Broadcast soul swap event."""
        await self.broadcast({
            "type": "soul_swap",
            "entity": entity_name,
            "tincture": tincture,
            "message": f"🧪 {entity_name} taking {tincture}"
        })
    
    async def broadcast_stats_update(self, stats: dict):
        """Broadcast facility statistics."""
        await self.broadcast({
            "type": "stats_update",
            "stats": stats
        })
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict]:
        """Get info about all connections."""
        return list(self.connection_info.values())
