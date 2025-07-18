# -*- coding: utf-8 -*-
"""
System logging utilities for AgentBeats scenarios.

This module handles system-level logging including agent readiness, errors,
startup, and shutdown events.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Import context management
from .context import DEFAULT_BACKEND_URL, get_battle_context





def log_ready(battle_id: str, agent_name: str, capabilities: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """Log agent readiness to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare ready event data for backend API
    ready_data: Dict[str, Any] = {
        "event_type": "agent_ready",
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if capabilities:
        ready_data["capabilities"] = capabilities
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/ready",
            json=ready_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully logged agent readiness for battle %s", battle_id)
            return 'readiness logged to backend'
        else:
            logger.error("Failed to log readiness to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[READY] [{timestamp}] {agent_name} is ready\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'readiness logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when logging readiness for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[READY] [{timestamp}] {agent_name} is ready\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'readiness logged locally (network error)'


def log_error(battle_id: str, error_message: str, error_type: str = "error", reported_by: str = "system", backend_url: Optional[str] = None) -> str:
    """Log an error event to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare error event data for backend API
    error_data = {
        "event_type": "error",
        "error_type": error_type,
        "error_message": error_message,
        "reported_by": reported_by,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/errors",
            json=error_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.error("Successfully logged error to backend for battle %s", battle_id)
            return 'error logged to backend'
        else:
            logger.error("Failed to log error to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[ERROR] [{timestamp}] {error_type.upper()}: {error_message}\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'error logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when logging error for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[ERROR] [{timestamp}] {error_type.upper()}: {error_message}\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'error logged locally (network error)'


def log_startup(battle_id: str, agent_name: str, config: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """Log agent startup to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare startup event data for backend API
    startup_data: Dict[str, Any] = {
        "event_type": "agent_startup",
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if config:
        startup_data["config"] = config
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/startup",
            json=startup_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully logged agent startup for battle %s", battle_id)
            return 'startup logged to backend'
        else:
            logger.error("Failed to log startup to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[STARTUP] [{timestamp}] {agent_name} starting up\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'startup logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when logging startup for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[STARTUP] [{timestamp}] {agent_name} starting up\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'startup logged locally (network error)'


def log_shutdown(battle_id: str, agent_name: str, reason: str = "normal", backend_url: Optional[str] = None) -> str:
    """Log agent shutdown to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare shutdown event data for backend API
    shutdown_data = {
        "event_type": "agent_shutdown",
        "agent_name": agent_name,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/shutdown",
            json=shutdown_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully logged agent shutdown for battle %s", battle_id)
            return 'shutdown logged to backend'
        else:
            logger.error("Failed to log shutdown to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[SHUTDOWN] [{timestamp}] {agent_name} shutting down: {reason}\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'shutdown logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when logging shutdown for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[SHUTDOWN] [{timestamp}] {agent_name} shutting down: {reason}\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'shutdown logged locally (network error)' 