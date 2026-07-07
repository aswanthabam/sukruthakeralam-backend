import json
import os
from datetime import datetime
from typing import Union
from loguru import logger

# Resolve the project root assuming this file is at core/payment/sbiepay/logger.py
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
LOG_DIR = os.path.join(BASE_DIR, "logs", "sbiepay")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Keep track of which actions we've added handlers for
_configured_actions = set()

def _ensure_action_handler(action: str):
    """
    Dynamically adds a file handler for the given action if it doesn't already exist.
    """
    if action not in _configured_actions:
        safe_action = "".join([c if c.isalnum() or c in ['_', '-'] else "_" for c in action])
        filename = os.path.join(LOG_DIR, f"{safe_action}.log")
        
        # Add a new file handler for this specific action
        # - format="{message}": We only want to log our JSON payload
        # - filter: Only log messages where extra["action"] matches this action
        # - enqueue=True: Safely handles multi-processing and multi-threading writes
        logger.add(
            filename,
            format="{message}",
            filter=lambda record: record["extra"].get("action") == action,
            rotation="00:00",
            retention="30 days",
            enqueue=True,
            encoding="utf-8"
        )
        _configured_actions.add(action)

def log_sbiepay_transaction(order_id: str, action: str, data: Union[dict, str]):
    """
    Logs SBIePay transaction details into an action-specific log file using Loguru.
    """
    try:
        _ensure_action_handler(action)
        
        timestamp = datetime.now().isoformat()
        
        # Try to parse string data as JSON if possible
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass
                
        # Since files are grouped by action, we must include the order_id in the payload
        log_entry = {
            "timestamp": timestamp,
            "order_id": order_id,
            "data": data
        }
        
        # Log it with the `action` bound to the `extra` dict so the filter catches it
        action_logger = logger.bind(action=action)
        action_logger.info(json.dumps(log_entry))
        
    except Exception as e:
        logger.error(f"Failed to write to sbiepay log for action {action}: {str(e)}")
