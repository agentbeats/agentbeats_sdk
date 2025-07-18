# -*- coding: utf-8 -*-
"""
Logging utilities for AgentBeats scenarios.

This module provides comprehensive logging functionality split into:
- Context management: battle context setup and management
- System logging: agent readiness, errors, startup/shutdown
- Interaction history: battle events, results, agent actions
"""

# Context management functions
from .context import (
    set_battle_context,
    auto_setup_mcp_logging,
    get_battle_context,
    clear_battle_context,
    
    # Constants and globals
    DEFAULT_BACKEND_URL,
    CURRENT_BATTLE_ID,
    CURRENT_AGENT_NAME,
    CURRENT_BACKEND_URL,
    CURRENT_MCP_TOOLS,
)

# System logging functions
from .logging import (
    log_ready,
    log_error,
    log_startup,
    log_shutdown,
    logger,
)

# Interaction history functions
from .interaction_history import (
    record_battle_event,
    record_battle_result,
    record_agent_action,
    record_monitoring_check,
    record_interaction,
)

__all__ = [
    # Context management
    'set_battle_context',
    'auto_setup_mcp_logging',
    'get_battle_context',
    'clear_battle_context',
    
    # System logs
    'log_ready',
    'log_error',
    'log_startup',
    'log_shutdown',
    
    # Interaction history
    'record_battle_event',
    'record_battle_result',
    'record_agent_action',
    'record_monitoring_check',
    'record_interaction',
    
    # Constants and globals
    'DEFAULT_BACKEND_URL',
    'CURRENT_BATTLE_ID',
    'CURRENT_AGENT_NAME', 
    'CURRENT_BACKEND_URL',
    'CURRENT_MCP_TOOLS',
    
    # Logger instance
    'logger',
] 