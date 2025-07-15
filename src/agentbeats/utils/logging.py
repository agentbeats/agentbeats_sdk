# -*- coding: utf-8 -*-
"""
MCP-based logging utilities for AgentBeats scenarios.
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

# Default backend URL - can be overridden
DEFAULT_BACKEND_URL = "http://localhost:9000"

# Global battle context - set by agents
CURRENT_BATTLE_ID = None
CURRENT_AGENT_NAME = None
CURRENT_BACKEND_URL = DEFAULT_BACKEND_URL
CURRENT_MCP_TOOLS = None  # MCP tools for logging


def set_battle_context(battle_id: str, agent_name: str = "system", backend_url: Optional[str] = None, mcp_tools: Optional[Dict] = None):
    """Set the current battle context for automatic logging."""
    global CURRENT_BATTLE_ID, CURRENT_AGENT_NAME, CURRENT_BACKEND_URL, CURRENT_MCP_TOOLS
    CURRENT_BATTLE_ID = battle_id
    CURRENT_AGENT_NAME = agent_name
    if backend_url:
        CURRENT_BACKEND_URL = backend_url
    if mcp_tools:
        CURRENT_MCP_TOOLS = mcp_tools


def _log_via_mcp_or_direct(message: str, detail: Optional[Dict[str, Any]] = None, is_result: bool = False, winner: Optional[str] = None):
    """Helper function to log via MCP tools if available, otherwise direct API."""
    if CURRENT_BATTLE_ID is None:
        return
    
    if CURRENT_MCP_TOOLS and not is_result:
        # Use MCP tool if available
        try:
            update_battle_process = CURRENT_MCP_TOOLS.get("update_battle_process")
            if update_battle_process:
                update_battle_process(
                    battle_id=CURRENT_BATTLE_ID,
                    message=message,
                    reported_by=CURRENT_AGENT_NAME or "system",
                    detail=detail
                )
                return
        except Exception as e:
            logger.warning(f"Failed to log via MCP tool: {e}")
    
    elif CURRENT_MCP_TOOLS and is_result and winner:
        # Use MCP result tool if available
        try:
            report_on_battle_end = CURRENT_MCP_TOOLS.get("report_on_battle_end")
            if report_on_battle_end:
                report_on_battle_end(
                    battle_id=CURRENT_BATTLE_ID,
                    message=message,
                    winner=winner,
                    detail=detail
                )
                return
        except Exception as e:
            logger.warning(f"Failed to log result via MCP tool: {e}")
    
    # Fallback to direct API call
    if is_result and winner:
        log_battle_result(CURRENT_BATTLE_ID, message, winner, detail, CURRENT_BACKEND_URL)
    else:
        log_battle_event(CURRENT_BATTLE_ID, message, CURRENT_AGENT_NAME or "system", detail, CURRENT_BACKEND_URL)


def auto_log(func=None, *, action_name: Optional[str] = None, include_args: bool = True, include_result: bool = True):
    """
    Decorator to automatically log function execution.
    
    Args:
        action_name: Custom name for the action (defaults to function name)
        include_args: Whether to include function arguments in the log
        include_result: Whether to include function result in the log
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if CURRENT_BATTLE_ID is None:
                # No battle context, just execute the function
                return func(*args, **kwargs)
            
            action = action_name or func.__name__
            
            # Prepare detail dict
            detail = {}
            if include_args:
                # Filter out sensitive args like passwords
                safe_args = []
                for arg in args:
                    if isinstance(arg, str) and any(sensitive in str(arg).lower() for sensitive in ['password', 'secret', 'key', 'token']):
                        safe_args.append('***')
                    else:
                        safe_args.append(str(arg))
                detail['args'] = safe_args
                detail['kwargs'] = {k: '***' if any(sensitive in k.lower() for sensitive in ['password', 'secret', 'key', 'token']) else v 
                                  for k, v in kwargs.items()}
            
            try:
                # Log function start
                _log_via_mcp_or_direct(
                    message=f"Starting {action}",
                    detail=detail
                )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Log success
                success_detail = detail.copy()
                if include_result:
                    success_detail['result'] = str(result)
                
                _log_via_mcp_or_direct(
                    message=f"Completed {action} successfully",
                    detail=success_detail
                )
                
                return result
                
            except Exception as e:
                # Log error
                error_detail = detail.copy()
                error_detail['error'] = str(e)
                error_detail['error_type'] = type(e).__name__
                
                _log_via_mcp_or_direct(
                    message=f"Failed to execute {action}: {str(e)}",
                    detail=error_detail
                )
                
                raise
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def log_battle_event(battle_id: str, message: str, reported_by: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """
    Log a battle event to the backend API and console.
    
    This function records intermediate events and progress during a battle, helping track
    what each participant is doing and how the battle is evolving.
    
    Args:
        battle_id (str): Unique identifier for the battle session
        message (str): Simple, human-readable description of what happened
        reported_by (str): The role/agent that triggered this event
        detail (dict, optional): Structured data containing specific details about the event
        backend_url (str, optional): Backend API URL (defaults to DEFAULT_BACKEND_URL)
    
    Returns:
        str: Status message indicating where the log was recorded
    
    Example usage:
        log_battle_event(
            battle_id="battle_123",
            message="Red agent launched attack",
            reported_by="red_agent",
            detail={"attack_type": "prompt_injection", "target": "blue_agent"}
        )
    """
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    # Prepare event data for backend API
    event_data = {
        "is_result": False,
        "message": message,
        "reported_by": reported_by,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if detail:
        event_data["detail"] = detail
    
    try:
        # Call backend API
        response = requests.post(
            f"{backend_url}/battles/{battle_id}",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully logged to backend for battle %s", battle_id)
            return 'logged to backend'
        else:
            logger.error("Failed to log to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[INFO] [{timestamp}] {message}\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when logging to backend for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[INFO] [{timestamp}] {message}\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'logged locally (network error)'


def log_battle_result(battle_id: str, message: str, winner: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """
    Report the final battle result to backend API.
    
    Args:
        battle_id (str): The battle ID
        message (str): Simple, human-readable description of what happened
        winner (str): The winner of the battle ("green", "blue", "red", or "draw")
        detail (dict, optional): Additional detail information
        backend_url (str, optional): Backend API URL (defaults to DEFAULT_BACKEND_URL)
    
    Returns:
        str: Status message indicating where the result was recorded
    
    Example usage:
        log_battle_result(
            battle_id="battle_123",
            message="Battle completed successfully",
            winner="red",
            detail={"final_score": 95, "duration": "2m30s"}
        )
    """
    backend_url = backend_url or DEFAULT_BACKEND_URL
    
    logger.info("Reporting battle result for %s: winner=%s", battle_id, winner)
    
    # Prepare result event data for backend API
    result_data = {
        "is_result": True,
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
            f"{backend_url}/battles/{battle_id}",
            json=result_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully reported battle result to backend for battle %s", battle_id)
            return f'battle result reported: winner={winner}'
        else:
            logger.error("Failed to report battle result to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[RESULT] [{timestamp}] Winner: {winner}\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'result logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when reporting battle result for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[RESULT] [{timestamp}] Winner: {winner}\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'result logged locally (network error)'


def log_error(battle_id: str, error_message: str, error_type: str = "error", reported_by: str = "system", backend_url: Optional[str] = None) -> str:
    """
    Log an error event to the backend API and console.
    
    Args:
        battle_id (str): Unique identifier for the battle session
        error_message (str): Description of the error that occurred
        error_type (str): Type of error ("error", "warning", "critical")
        reported_by (str): The role/agent that encountered the error
        backend_url (str, optional): Backend API URL (defaults to DEFAULT_BACKEND_URL)
    
    Returns:
        str: Status message indicating where the error was logged
    
    Example usage:
        log_error(
            battle_id="battle_123",
            error_message="Failed to connect to SSH host",
            error_type="error",
            reported_by="red_agent"
        )
    """
    detail = {
        "error_type": error_type,
        "error_message": error_message
    }
    
    return log_battle_event(
        battle_id=battle_id,
        message=f"Error: {error_message}",
        reported_by=reported_by,
        detail=detail,
        backend_url=backend_url
    )


def log_agent_action(battle_id: str, action: str, agent_name: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """
    Log an agent action to the backend API and console.
    
    Args:
        battle_id (str): Unique identifier for the battle session
        action (str): Description of the action performed
        agent_name (str): Name of the agent performing the action
        detail (dict, optional): Additional details about the action
        backend_url (str, optional): Backend API URL (defaults to DEFAULT_BACKEND_URL)
    
    Returns:
        str: Status message indicating where the action was logged
    
    Example usage:
        log_agent_action(
            battle_id="battle_123",
            action="Created web service on port 80",
            agent_name="red_agent",
            detail={"port": 80, "service_type": "http"}
        )
    """
    return log_battle_event(
        battle_id=battle_id,
        message=f"{agent_name}: {action}",
        reported_by=agent_name,
        detail=detail,
        backend_url=backend_url
    )


def log_monitoring_check(battle_id: str, check_number: int, total_checks: int, status: str, detail: Optional[Dict[str, Any]] = None, backend_url: Optional[str] = None) -> str:
    """
    Log a monitoring check result to the backend API and console.
    
    Args:
        battle_id (str): Unique identifier for the battle session
        check_number (int): Current check number
        total_checks (int): Total number of checks
        status (str): Status of the monitoring check ("success", "failure", "partial")
        detail (dict, optional): Additional details about the check
        backend_url (str, optional): Backend API URL (defaults to DEFAULT_BACKEND_URL)
    
    Returns:
        str: Status message indicating where the check was logged
    
    Example usage:
        log_monitoring_check(
            battle_id="battle_123",
            check_number=5,
            total_checks=24,
            status="success",
            detail={"uptime_percentages": {"red_agent": 95, "blue_agent": 87}}
        )
    """
    message = f"Monitoring check {check_number}/{total_checks}: {status}"
    
    if detail is None:
        detail = {}
    detail["check_number"] = check_number
    detail["total_checks"] = total_checks
    detail["status"] = status
    
    return log_battle_event(
        battle_id=battle_id,
        message=message,
        reported_by="green_agent",
        detail=detail,
        backend_url=backend_url
    ) 