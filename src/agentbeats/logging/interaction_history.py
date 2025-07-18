# -*- coding: utf-8 -*-
"""
Interaction history utilities for AgentBeats scenarios.

This module handles recording battle events, results, and agent actions
for interaction history and analysis.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Import context management
from .context import DEFAULT_BACKEND_URL, get_battle_context


def record_battle_event(battle_id: str, message: str, reported_by: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """Record a battle event to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare event data for backend API
    event_data: Dict[str, Any] = {
        "event_type": "battle_event",
        "message": message,
        "reported_by": reported_by,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if detail:
        event_data["detail"] = detail
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/events",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully recorded battle event for battle %s", battle_id)
            return 'event recorded to backend'
        else:
            logger.error("Failed to record battle event to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[EVENT] [{timestamp}] {reported_by}: {message}\n"
            with open(f"{battle_id}_events.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'event recorded locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when recording battle event for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[EVENT] [{timestamp}] {reported_by}: {message}\n"
        with open(f"{battle_id}_events.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'event recorded locally (network error)'


def record_battle_result(battle_id: str, message: str, winner: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """Record the final battle result to backend API."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    logger.info("Recording battle result for %s: winner=%s", battle_id, winner)
    
    # Prepare result event data for backend API
    result_data: Dict[str, Any] = {
        "event_type": "battle_result",
        "message": message,
        "winner": winner,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reported_by": "green_agent"  # Assuming the green agent reports the result
    }
    
    if detail:
        result_data["detail"] = detail
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/result",
            json=result_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully recorded battle result to backend for battle %s", battle_id)
            return f'battle result recorded: winner={winner}'
        else:
            logger.error("Failed to record battle result to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[RESULT] [{timestamp}] Winner: {winner} - {message}\n"
            with open(f"{battle_id}_events.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'result recorded locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when recording battle result for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[RESULT] [{timestamp}] Winner: {winner} - {message}\n"
        with open(f"{battle_id}_events.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'result recorded locally (network error)'


def record_agent_action(battle_id: str, action: str, agent_name: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """Record an agent action to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare action event data for backend API
    action_data: Dict[str, Any] = {
        "event_type": "agent_action",
        "action": action,
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if detail:
        action_data["detail"] = detail
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/actions",
            json=action_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully recorded agent action for battle %s", battle_id)
            return 'action recorded to backend'
        else:
            logger.error("Failed to record agent action to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[ACTION] [{timestamp}] {agent_name}: {action}\n"
            with open(f"{battle_id}_actions.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'action recorded locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when recording agent action for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[ACTION] [{timestamp}] {agent_name}: {action}\n"
        with open(f"{battle_id}_actions.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'action recorded locally (network error)'


def record_monitoring_check(battle_id: str, check_number: int, total_checks: int, status: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """Record a monitoring check result to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    message = f"Monitoring check {check_number}/{total_checks}: {status}"
    
    if detail is None:
        detail = {}
    detail["check_number"] = check_number
    detail["total_checks"] = total_checks
    detail["status"] = status
    
    # Prepare monitoring event data for backend API
    monitoring_data = {
        "event_type": "monitoring_check",
        "message": message,
        "reported_by": "green_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "detail": detail
    }
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/monitoring",
            json=monitoring_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully recorded monitoring check for battle %s", battle_id)
            return 'monitoring check recorded to backend'
        else:
            logger.error("Failed to record monitoring check to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[MONITOR] [{timestamp}] {message}\n"
            with open(f"{battle_id}_monitoring.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'monitoring check recorded locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when recording monitoring check for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[MONITOR] [{timestamp}] {message}\n"
        with open(f"{battle_id}_monitoring.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'monitoring check recorded locally (network error)'


def record_interaction(battle_id: str, interaction_type: str, from_agent: str, to_agent: str, content: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """Record an interaction between agents to the backend API and console."""
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare interaction event data for backend API
    interaction_data: Dict[str, Any] = {
        "event_type": "interaction",
        "interaction_type": interaction_type,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "content": content,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if detail:
        interaction_data["detail"] = detail
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}/interactions",
            json=interaction_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully recorded interaction for battle %s", battle_id)
            return 'interaction recorded to backend'
        else:
            logger.error("Failed to record interaction to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[INTERACTION] [{timestamp}] {from_agent} -> {to_agent} ({interaction_type}): {content}\n"
            with open(f"{battle_id}_interactions.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'interaction recorded locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when recording interaction for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[INTERACTION] [{timestamp}] {from_agent} -> {to_agent} ({interaction_type}): {content}\n"
        with open(f"{battle_id}_interactions.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'interaction recorded locally (network error)' 