# -*- coding: utf-8 -*-
"""
SSH utilities for AgentBeats scenarios.
"""

import paramiko
from typing import Dict, Any


def _execute_ssh_command_helper(ssh_client, command: str) -> str:
    """
    Helper function to execute SSH command and format output.
    """
    try:
        # Execute command
        stdin, stdout, stderr = ssh_client.exec_command(command)
        
        # Get output
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        # Wait for command to complete
        exit_status = stdout.channel.recv_exit_status()
        
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




async def test_ssh_connection(host: str, credentials: Dict[str, str]) -> bool:
    """
    Test if SSH connection can be established.
    """
    
    try:
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
        
        # Close connection
        ssh_client.close()
        return True
        
    except Exception as e:
        return False 