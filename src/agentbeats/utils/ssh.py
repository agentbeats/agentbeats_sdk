# -*- coding: utf-8 -*-
"""
SSH utilities for AgentBeats scenarios.
"""

from typing import Dict, Any
from .logging import auto_log


@auto_log(action_name="SSH Command Execution")
def _execute_ssh_command_helper(ssh_client, command: str) -> str:
    """
    Helper function to execute SSH command and format output.
    """
    from .logging import log_battle_event, CURRENT_BATTLE_ID, CURRENT_AGENT_NAME, CURRENT_BACKEND_URL
    
    try:
        # Log the command being executed
        if CURRENT_BATTLE_ID:
            from .logging import _log_via_mcp_or_direct
            _log_via_mcp_or_direct(
                message=f"Executing SSH command: {command}",
                detail={"command": command}
            )
        
        # Execute command
        stdin, stdout, stderr = ssh_client.exec_command(command)
        
        # Get output
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        # Wait for command to complete
        exit_status = stdout.channel.recv_exit_status()
        
        # Log the results
        if CURRENT_BATTLE_ID:
            from .logging import _log_via_mcp_or_direct
            _log_via_mcp_or_direct(
                message=f"SSH command completed with exit status {exit_status}",
                detail={
                    "command": command,
                    "exit_status": exit_status,
                    "output_length": len(output),
                    "error_length": len(error),
                    "output_preview": output[:200] + "..." if len(output) > 200 else output,
                    "error_preview": error[:200] + "..." if len(error) > 200 else error
                }
            )
        
        result = f"Command: {command}\nExit Status: {exit_status}\n"
        
        if output:
            result += f"Output:\n{output}\n"
        
        if error:
            result += f"Error:\n{error}\n"
        
        if exit_status == 0:
            return f"✅ {result}"
        else:
            return f"⚠️ {result}"
            
    except Exception as e:
        # Log the error
        if CURRENT_BATTLE_ID:
            from .logging import _log_via_mcp_or_direct
            _log_via_mcp_or_direct(
                message=f"SSH command execution failed: {str(e)}",
                detail={"error": str(e), "error_type": "error"}
            )
        return f"SSH Command Error: {str(e)}"


def create_ssh_connect_tool(agent_instance: Any, default_host: str = "localhost", default_port: int = 22, default_username: str = "root", default_password: str = "") -> Any:
    """
    Create an SSH connection tool for an agent.
    """
    from agents import function_tool
    
    @function_tool(name_override="connect_to_ssh_host")
    def connect_to_ssh_host(host: str = default_host, port: int = default_port, username: str = default_username, password: str = default_password) -> str:
        """
        Connect to an SSH host.
        This establishes a connection to the remote system where you can execute commands.
        """
        try:
            import paramiko
            
            # Create SSH client
            agent_instance.ssh_client = paramiko.SSHClient()
            agent_instance.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the host
            agent_instance.ssh_client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10
            )
            
            # Test the connection
            test_result = _execute_ssh_command_helper(agent_instance.ssh_client, "echo 'SSH connection successful' && pwd")
            
            if test_result.startswith("❌"):
                return test_result
            
            agent_instance.ssh_connected = True
            return f"✅ Successfully connected to SSH host {host}:{port}\n{test_result}"
            
        except Exception as e:
            return f"❌ Failed to connect to SSH host: {str(e)}"
    
    return connect_to_ssh_host


def create_ssh_command_tool(agent_instance: Any) -> Any:
    """
    Create an SSH command execution tool for an agent.
    """
    from agents import function_tool
    
    @function_tool(name_override="execute_ssh_command")
    def execute_ssh_command(command: str) -> str:
        """
        Execute a command directly in the SSH terminal of the connected host.
        """
        if not hasattr(agent_instance, 'ssh_connected') or not agent_instance.ssh_connected:
            return "❌ Not connected to SSH host. Use connect_to_ssh_host first."
        
        return _execute_ssh_command_helper(agent_instance.ssh_client, command)
    
    return execute_ssh_command




@auto_log(action_name="SSH Connection Test")
async def test_ssh_connection(host: str, credentials: Dict[str, str]) -> bool:
    """
    Test if SSH connection can be established.
    """
    from .logging import log_battle_event, CURRENT_BATTLE_ID, CURRENT_AGENT_NAME, CURRENT_BACKEND_URL
    
    try:
        import paramiko
        
        # Log connection attempt
        if CURRENT_BATTLE_ID:
            log_battle_event(
                battle_id=CURRENT_BATTLE_ID,
                message=f"Attempting SSH connection to {host}:{credentials.get('port', 22)}",
                reported_by=CURRENT_AGENT_NAME or "system",
                detail={
                    "host": host,
                    "port": credentials.get("port", 22),
                    "username": credentials.get("username", "root"),
                    "timeout": 10
                },
                backend_url=CURRENT_BACKEND_URL
            )
        
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the host
        port = credentials.get("port", 22)
        if isinstance(port, str):
            port = int(port)
            
        ssh_client.connect(
            hostname=host,
            port=port,
            username=credentials.get("username", "root"),
            password=credentials.get("password", ""),
            timeout=10
        )
        
        # Log successful connection
        if CURRENT_BATTLE_ID:
            log_battle_event(
                battle_id=CURRENT_BATTLE_ID,
                message=f"SSH connection successful to {host}:{port}",
                reported_by=CURRENT_AGENT_NAME or "system",
                detail={
                    "host": host,
                    "port": port,
                    "username": credentials.get("username", "root")
                },
                backend_url=CURRENT_BACKEND_URL
            )
        
        # Close connection
        ssh_client.close()
        return True
        
    except Exception as e:
        # Log connection failure
        if CURRENT_BATTLE_ID:
            from .logging import log_error
            log_error(
                battle_id=CURRENT_BATTLE_ID,
                error_message=f"SSH connection failed to {host}: {str(e)}",
                error_type="error",
                reported_by=CURRENT_AGENT_NAME or "system",
                backend_url=CURRENT_BACKEND_URL
            )
        return False 