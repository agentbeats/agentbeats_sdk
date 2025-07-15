# -*- coding: utf-8 -*-

from .agentbeats.agent_executor import *
from .agentbeats.agent_launcher import *
from .agentbeats.utils.agents import (
    create_a2a_client, send_message_to_agent, send_message_to_agents,
    check_agent_health, ping_agents
)
from .agentbeats.utils.environment import (
    setup_docker_environment, cleanup_docker_environment, check_container_health,
    execute_ssh_command, create_ssh_session, SSHSession, setup_game_arena, teardown_game_arena
)

_TOOL_REGISTRY = [] # global register for tools

def tool(func=None):
    """
    Usage: @agentbeats.tool() or @agentbeats.tool
    A decorator to register a function as a tool in the agentbeats SDK.
    This function can be used to register any callable that should be treated as a tool.
    """
    def _decorator(func):
        _TOOL_REGISTRY.append(func)
        return func

    if func is not None and callable(func):
        return _decorator(func)

    return _decorator

def get_registered_tools():
    return list(_TOOL_REGISTRY)
