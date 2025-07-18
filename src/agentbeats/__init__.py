# -*- coding: utf-8 -*-

from .agent_executor import *
from .agent_launcher import *
from .utils.agents import (
    create_a2a_client, send_message_to_agent, send_message_to_agents
)
from .utils.environment import (
    setup_container, cleanup_container, check_container_health
)
from .utils.ssh import (
    _execute_ssh_command_helper, create_ssh_connect_tool, execute_ssh_command, test_ssh_connection
)
from .logging import (
    set_battle_context, log_ready, log_error, log_startup, log_shutdown,
    record_battle_event, record_battle_result, record_agent_action,
    record_monitoring_check, record_interaction
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
