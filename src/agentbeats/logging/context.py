# -*- coding: utf-8 -*-
"""
Battle context management for AgentBeats logging.

This module handles the global battle context that is shared between
system logging and interaction history modules.
"""

import logging
from typing import Dict, Any, Optional

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
        print(f"🔧 Set up battle context with {len(mcp_tools)} MCP tools for {agent_name}")
    else:
        print(f"🔧 Set up battle context without MCP tools for {agent_name}")


def auto_setup_mcp_logging(battle_id: str, agent_name: str = "system", backend_url: Optional[str] = None):
    """Automatically set up battle context and try to detect MCP tools from environment."""
    global CURRENT_MCP_TOOLS
    
    # Try to detect MCP tools from environment variables or other sources
    mcp_tools = None
    
    # Check if we're running in an agent context with MCP servers
    # This is a simplified approach - in a real implementation, you'd need to
    # access the agent's MCP server context
    try:
        # For now, we'll set up basic context and let the agent pass MCP tools manually
        set_battle_context(battle_id, agent_name, backend_url, mcp_tools)
        print(f"🔧 Auto-setup complete for {agent_name}. Use setup_battle_logging with MCP tools JSON if available.")
    except Exception as e:
        print(f"⚠️ Auto-setup failed: {e}")
        # Fallback to basic setup
        set_battle_context(battle_id, agent_name, backend_url, None)


def get_battle_context():
    """Get the current battle context."""
    return CURRENT_BATTLE_ID, CURRENT_AGENT_NAME, CURRENT_BACKEND_URL, CURRENT_MCP_TOOLS


def clear_battle_context():
    """Clear the current battle context."""
    global CURRENT_BATTLE_ID, CURRENT_AGENT_NAME, CURRENT_BACKEND_URL, CURRENT_MCP_TOOLS
    CURRENT_BATTLE_ID = None
    CURRENT_AGENT_NAME = None
    CURRENT_BACKEND_URL = DEFAULT_BACKEND_URL
    CURRENT_MCP_TOOLS = None
    logger.info("Battle context cleared") 