"""
WebSocket Client for sending vision metrics to the FastAPI backend.

Features:
- Async implementation using asyncio and websockets library
- Automatic reconnection with exponential backoff
- Heartbeat/ping to detect dead connections
- Thread-safe metric submission from the CV pipeline thread
- Configurable send interval (default 500ms)
"""

import json
import time
import asyncio
import logging
import threading
from typing import Optional, Dict, Any
from collections import deque

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    Async WebSocket client for streaming vision metrics.
    
    Runs in a dedicated thread with its own asyncio event loop.
    The CV pipeline thread calls send_metrics() which is thread-safe.
    
    Usage:
        client = WebSocketClient(url="ws://localhost:8000/ws/vision")
        client.start()
        
        # From CV pipeline thread:
        client.send_metrics({"face_visible": True, "engagement": 82})
        
        # Shutdown:
        client.stop()
    """
    
    def __init__(
        self,
        url: str = "ws://localhost:8000/ws/vision",
        send_interval: float = 0.5,
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 30.0,
        heartbeat_interval: float = 10.0,
        max_queue_size: int = 100,
    ):
        """
        Args:
            url: WebSocket server URL.
            send_interval: Minimum interval between sends (seconds).
            reconnect_base_delay: Initial reconnection delay (seconds).
            reconnect_max_delay: Maximum reconnection delay (seconds).
            heartbeat_interval: Interval for ping/heartbeat (seconds).
            max_queue_size: Maximum queued metrics before dropping old ones.
        """
        self._url = url
        self._send_interval = send_interval
        self._reconnect_base = reconnect_base_delay
        self._reconnect_max = reconnect_max_delay
        self._heartbeat_interval = heartbeat_interval
        
        # Thread-safe metric queue
        self._queue: deque = deque(maxlen=max_queue_size)
        self._queue_lock = threading.Lock()
        
        # State
        self._running = False
        self._connected = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._last_send_time = 0.0
        self._reconnect_attempts = 0
        
        logger.info(f"WebSocketClient initialized: url={url}")
    
    def start(self) -> None:
        """Start the WebSocket client in a background thread."""
        if self._running:
            logger.warning("WebSocket client already running")
            return
        
        if not HAS_WEBSOCKETS:
            logger.error(
                "websockets library not installed. "
                "Install with: pip install websockets"
            )
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._run_event_loop,
            name="WebSocketClient",
            daemon=True,
        )
        self._thread.start()
        logger.info("WebSocket client started")
    
    def stop(self) -> None:
        """Stop the WebSocket client."""
        self._running = False
        if self._loop and not self._loop.is_closed():
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except RuntimeError:
                pass  # Loop might have been closed concurrently
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("WebSocket client stopped")
    
    def send_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Queue metrics for sending (thread-safe).
        
        Called from the CV pipeline thread. Metrics are queued and
        sent asynchronously by the WebSocket thread.
        
        Args:
            metrics: Dictionary of vision metrics to send.
        """
        with self._queue_lock:
            self._queue.append(metrics)
    
    @property
    def is_connected(self) -> bool:
        """Whether the WebSocket is currently connected."""
        return self._connected
    
    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._connection_loop())
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            self._loop.close()
    
    async def _connection_loop(self) -> None:
        """
        Main connection loop with automatic reconnection.
        
        Uses exponential backoff for reconnection delays:
            delay = min(base * 2^attempts, max_delay)
        """
        while self._running:
            try:
                async with websockets.connect(
                    self._url,
                    ping_interval=self._heartbeat_interval,
                    ping_timeout=self._heartbeat_interval * 2,
                    close_timeout=5,
                ) as ws:
                    self._connected = True
                    self._reconnect_attempts = 0
                    logger.info(f"Connected to {self._url}")
                    
                    await self._send_loop(ws)
                    
            except ConnectionRefusedError:
                logger.warning(
                    f"Connection refused to {self._url}"
                )
            except Exception as e:
                logger.warning(f"WebSocket error: {e}")
            finally:
                self._connected = False
            
            if not self._running:
                break
            
            # Exponential backoff
            delay = min(
                self._reconnect_base * (2 ** self._reconnect_attempts),
                self._reconnect_max,
            )
            self._reconnect_attempts += 1
            logger.info(
                f"Reconnecting in {delay:.1f}s "
                f"(attempt {self._reconnect_attempts})"
            )
            await asyncio.sleep(delay)
    
    async def _send_loop(self, ws) -> None:
        """
        Send queued metrics at the configured interval.
        """
        while self._running:
            now = time.monotonic()
            
            # Check if it's time to send
            if now - self._last_send_time >= self._send_interval:
                metrics = self._get_latest_metrics()
                if metrics:
                    try:
                        await ws.send(json.dumps(metrics))
                        self._last_send_time = now
                    except Exception as e:
                        logger.warning(f"Send error: {e}")
                        return  # Will trigger reconnection
            
            # Small sleep to prevent busy-waiting
            await asyncio.sleep(0.05)
    
    def _get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent metrics from the queue, discarding older ones.
        Thread-safe.
        """
        with self._queue_lock:
            if not self._queue:
                return None
            # Take the latest, discard the rest
            latest = self._queue[-1]
            self._queue.clear()
            return latest
    
    def __enter__(self) -> 'WebSocketClient':
        self.start()
        return self
    
    def __exit__(self, *args) -> None:
        self.stop()
    
    def __del__(self) -> None:
        self.stop()
