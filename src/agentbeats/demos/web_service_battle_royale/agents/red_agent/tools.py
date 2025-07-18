# -*- coding: utf-8 -*-
"""
Battle Royale Red Agent Tools
This agent competes in the battle royale by SSHing into the battle arena
and creating a web service on port 80 serving its own name.
"""

import json
import time
import agentbeats as ab
from typing import Dict, Any

# Import SDK utilities
from agentbeats.utils.commands import SSHClient

# Agent state
agent_state = {
    "agent_id": None,
    "ssh_connected": False,
    "web_service_running": False,
    "service_id": None,
    "ssh_client": None,
    "ssh_tools_added": False,
    "battle_id": None,
    "ssh_credentials": None,
    "ssh_connect_tool": None,
    "ssh_command_tool": None
}

@ab.tool
def set_agent_id(agent_id: str) -> str:
    """Set the agent ID for this red agent."""
    try:
        agent_state["agent_id"] = agent_id
        
        # Log agent ID setup
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Agent ID set to: {agent_id}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"agent_id": agent_id} # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"🎯 Agent ID set to: {agent_id}")
        return f"✅ Agent ID set to: {agent_id}"
    except Exception as e:
        return f"❌ Failed to set agent ID: {str(e)}"


@ab.tool
def handle_battle_start(battle_info_json: str) -> str:
    """Handle battle start message from green agent."""
    try:
        battle_info = json.loads(battle_info_json)
        
        # Extract battle information
        battle_id = battle_info.get("battle_id")
        agent_id = battle_info.get("agent_id")
        ssh_credentials = battle_info.get("ssh_credentials")
        instructions = battle_info.get("instructions")
        
        # Note: Logging is handled by the green agent, no need to set up here
        
        # Set agent ID first
        if agent_id:
            set_agent_id(agent_id)
            print(f"🎯 Agent ID set to: {agent_id}")
        else:
            return "❌ No agent ID provided in battle info"
        
        # Connect to battle arena
        if ssh_credentials:
            host = ssh_credentials.get("host")
            port = ssh_credentials.get("port")
            username = ssh_credentials.get("username")
            password = ssh_credentials.get("password")
            
            if all([host, port, username, password]):
                connect_result = connect_to_battle_arena(host, port, username, password)
                if connect_result.startswith("✅"):
                    # Start own service (no blocking)
                    create_result = create_web_service()
                    return f"✅ Battle started successfully!\n{connect_result}\n{create_result}"
                else:
                    return f"❌ Failed to connect to battle arena: {connect_result}"
        
        return f"✅ Battle start message processed. Instructions: {instructions}"
        
    except Exception as e:
        return f"❌ Failed to handle battle start: {str(e)}"





@ab.tool
def setup_battle_logging(battle_id: str, mcp_tools_json: str = "") -> str:
    """Set up battle logging context with MCP tools."""
    try:
        # Parse MCP tools if provided
        mcp_tools = None
        if mcp_tools_json:
            try:
                mcp_tools = json.loads(mcp_tools_json)
                print(f"🔧 Received {len(mcp_tools)} MCP tools for logging")
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse MCP tools JSON: {mcp_tools_json}")
        
        # Set up battle context for logging
        # set_battle_context( # Removed as per new_code
        #     battle_id=battle_id, # Removed as per new_code
        #     agent_name="red_agent", # Removed as per new_code
        #     backend_url="http://localhost:9000", # Removed as per new_code
        #     mcp_tools=mcp_tools # Removed as per new_code
        # ) # Removed as per new_code
        
        agent_state["battle_id"] = battle_id
        agent_state["mcp_tools"] = mcp_tools
        
        # Log the setup completion
        # log_battle_event( # Removed as per new_code
        #     battle_id=battle_id, # Removed as per new_code
        #     message="Battle logging setup completed", # Removed as per new_code
        #     reported_by="red_agent", # Removed as per new_code
        #     detail={ # Removed as per new_code
        #         "mcp_tools_count": len(mcp_tools) if mcp_tools else 0, # Removed as per new_code
        #         "setup_method": "with_mcp_tools" # Removed as per new_code
        #     } # Removed as per new_code
        # ) # Removed as per new_code
        
        print(f"🔧 Set up battle logging for battle {battle_id} with {len(mcp_tools) if mcp_tools else 0} MCP tools")
        return f"✅ Battle logging setup complete for battle {battle_id}"
    except Exception as e:
        return f"❌ Failed to setup battle logging: {str(e)}"





@ab.tool
def connect_to_battle_arena(host: str, port: int, username: str, password: str) -> str:
    """Connect to the battle arena via SSH."""
    try:
        # Log connection attempt
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Attempting SSH connection to {host}:{port}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={ # Removed as per new_code
        #             "host": host, # Removed as per new_code
        #             "port": port, # Removed as per new_code
        #             "username": username, # Removed as per new_code
        #             "timeout": 10 # Removed as per new_code
        #         } # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"🔌 Connecting to battle arena at {username}@{host}:{port}")
        
        # Store credentials for later use
        agent_state["ssh_credentials"] = {
            "host": host,
            "port": port,
            "username": username,
            "password": password
        }
        
        # Create SSH client using the SDK
        credentials = {
            "username": username,
            "password": password,
            "port": port
        }
        
        ssh_client = SSHClient(host, credentials)
        connection_successful = ssh_client.connect()
        
        if connection_successful:
            # Store the SSH client
            agent_state["ssh_client"] = ssh_client
            agent_state["ssh_connected"] = True
            
            # Log successful connection
            # if CURRENT_BATTLE_ID: # Removed as per new_code
            #     log_battle_event( # Removed as per new_code
            #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
            #         message=f"SSH connection successful to {host}:{port}", # Removed as per new_code
            #         reported_by="red_agent", # Removed as per new_code
            #         detail={ # Removed as per new_code
            #             "host": host, # Removed as per new_code
            #             "port": port, # Removed as per new_code
            #             "username": username # Removed as per new_code
            #         } # Removed as per new_code
            #     ) # Removed as per new_code
            
            print(f"✅ Successfully connected to battle arena")
            return f"✅ Connected to battle arena at {username}@{host}:{port}"
        else:
            # Log connection failure
            # if CURRENT_BATTLE_ID: # Removed as per new_code
            #     log_battle_event( # Removed as per new_code
            #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
            #         message=f"SSH connection failed to {host}:{port}", # Removed as per new_code
            #         reported_by="red_agent", # Removed as per new_code
            #         detail={ # Removed as per new_code
            #             "error": "SSH connection test failed", # Removed as per new_code
            #             "error_type": "error", # Removed as per new_code
            #             "host": host, # Removed as per new_code
            #             "port": port, # Removed as per new_code
            #             "username": username # Removed as per new_code
            #         } # Removed as per new_code
            #     ) # Removed as per new_code
            raise Exception("SSH connection test failed")
        
    except Exception as e:
        # Log connection error
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Failed to connect to battle arena: {str(e)}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"error": str(e), "host": host, "port": port, "username": username} # Removed as per new_code
        #     ) # Removed as per new_code
        print(f"❌ Failed to connect to battle arena: {str(e)}")
        return f"❌ SSH connection failed: {str(e)}"


@ab.tool
def execute_ssh_command(command: str) -> str:
    """Execute a command on the battle arena via SSH."""
    try:
        if not agent_state["ssh_connected"]:
            return "❌ Not connected to battle arena. Connect first."
        
        # Log command execution
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Executing SSH command: {command}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"command": command} # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"💻 Executing SSH command: {command}")
        
        ssh_client = agent_state["ssh_client"]
        result = ssh_client.execute(command)
        
        # Log command result
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"SSH command completed", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={ # Removed as per new_code
        #             "command": command, # Removed as per new_code
        #             "result_preview": result[:200] + "..." if len(result) > 200 else result # Removed as per new_code
        #         } # Removed as per new_code
        #     ) # Removed as per new_code
        
        if result.startswith("Success:"):
            print(f"✅ SSH command executed successfully")
            return result
        else:
            print(f"⚠️ SSH command failed")
            return result
            
    except Exception as e:
        # Log command error
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"SSH command execution failed: {str(e)}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"error": str(e), "error_type": "error", "command": command} # Removed as per new_code
        #     ) # Removed as per new_code
        print(f"❌ SSH command error: {str(e)}")
        return f"❌ SSH command error: {str(e)}"


@ab.tool
def create_web_service() -> str:
    """Create a web service on port 80 serving the agent's name."""
    try:
        if not agent_state["ssh_connected"]:
            return "❌ Not connected to battle arena. Connect first."
        
        # Log web service creation start
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Starting web service creation", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"service_port": 80, "service_name": "Red Agent Web Service"} # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"🌐 Creating web service on port 80")
        
        # Clean up any existing services first
        print("🧹 Cleaning up any existing services...")
        execute_ssh_command("pkill -f 'red_agent_service.py' 2>/dev/null || true")
        execute_ssh_command("fuser -k 80/tcp 2>/dev/null || true")
        time.sleep(2)  # Wait for cleanup
        
        # Get agent ID for the service
        agent_id = agent_state.get("agent_id", "red_agent")
        
        # Debug: Print the agent ID being used
        print(f"🔍 Using agent ID: '{agent_id}' (type: {type(agent_id)})")
        
        if not agent_id or agent_id == "red_agent":
            return "❌ Agent ID not properly set. Cannot create web service."
        
        # Create a simple web service using Python
        service_script = f'''#!/usr/bin/env python3
import http.server
import socketserver

AGENT_ID = "{agent_id}"

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response = f"<h1>{{AGENT_ID}}</h1><p>This is the {{AGENT_ID}} web service running on port 80!</p>"
        self.wfile.write(response.encode('utf-8'))

PORT = 80
Handler = MyHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running on port {{PORT}}")
    httpd.serve_forever()
'''
        
        # Write service script to remote server
        ssh_client = agent_state["ssh_client"]
        sftp = ssh_client.open_sftp()
        
        # Create service file
        with sftp.file('/tmp/red_agent_service.py', 'w') as f:
            f.write(service_script)
        
        # Make it executable
        execute_ssh_command("chmod +x /tmp/red_agent_service.py")
        
        # Start the service in background
        execute_ssh_command("nohup python3 /tmp/red_agent_service.py > /tmp/red_agent_service.log 2>&1 &")
        
        # Wait a moment for service to start
        time.sleep(3)
        
        # Check service log for errors
        log_result = execute_ssh_command("cat /tmp/red_agent_service.log")
        print(f"🔍 Service log: {log_result}")
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Service log output", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"command": "cat /tmp/red_agent_service.log", "output": log_result} # Removed as per new_code
        #     ) # Removed as per new_code
        
        # Check if service process is running
        ps_result = execute_ssh_command("ps aux | grep red_agent_service.py | grep -v grep")
        print(f"🔍 Process check: {ps_result}")
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Process check output", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"command": "ps aux | grep red_agent_service.py | grep -v grep", "output": ps_result} # Removed as per new_code
        #     ) # Removed as per new_code
        
        # Check if service is running
        result = execute_ssh_command("curl -s http://localhost:80")
        print(f"🔍 Curl result: '{result}'")
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Curl command output", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"command": "curl -s http://localhost:80", "output": result} # Removed as per new_code
        #     ) # Removed as per new_code
        
        agent_id = agent_state.get("agent_id", "red_agent")
        if agent_id in result:
            agent_state["web_service_running"] = True
            
            # Log successful web service creation
            # if CURRENT_BATTLE_ID: # Removed as per new_code
            #     log_battle_event( # Removed as per new_code
            #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
            #         message="Web service created and running successfully", # Removed as per new_code
            #         reported_by="red_agent", # Removed as per new_code
            #         detail={"service_port": 80, "service_status": "running"} # Removed as per new_code
            #     ) # Removed as per new_code
            
            print(f"✅ Web service created and running on port 80")
            return f"✅ Web service created and running on port 80"
        else:
            # Log web service creation failure
            # if CURRENT_BATTLE_ID: # Removed as per new_code
            #     log_battle_event( # Removed as per new_code
            #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
            #         message="Web service failed to start", # Removed as per new_code
            #         reported_by="red_agent", # Removed as per new_code
            #         detail={"service_port": 80, "service_status": "failed"} # Removed as per new_code
            #     ) # Removed as per new_code
            
            print(f"❌ Web service failed to start")
            return f"❌ Web service failed to start"
            
    except Exception as e:
        # Log web service creation error
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Error creating web service: {str(e)}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"error": str(e), "service_port": 80} # Removed as per new_code
        #     ) # Removed as per new_code
        print(f"❌ Error creating web service: {str(e)}")
        return f"❌ Error creating web service: {str(e)}"


@ab.tool
def check_service_status() -> str:
    """Check if the web service is running."""
    try:
        if not agent_state["ssh_connected"]:
            return "❌ Not connected to battle arena. Connect first."
        
        # Log service status check
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Checking web service status", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"service_port": 80} # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"🔍 Checking web service status")
        
        # Check if service is responding
        result = execute_ssh_command("curl -s http://localhost:80")
        print(f"🔍 Curl result: '{result}'")
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Curl command output (status check)", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"command": "curl -s http://localhost:80", "output": result} # Removed as per new_code
        #     ) # Removed as per new_code
        
        agent_id = agent_state.get("agent_id", "red_agent")
        if agent_id in result:
            agent_state["web_service_running"] = True
            
            # Log service running
            # if CURRENT_BATTLE_ID: # Removed as per new_code
            #     log_battle_event( # Removed as per new_code
            #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
            #         message="Web service is running and responding", # Removed as per new_code
            #         reported_by="red_agent", # Removed as per new_code
            #         detail={"service_port": 80, "service_status": "running"} # Removed as per new_code
            #     ) # Removed as per new_code
            
            print(f"✅ Web service is running")
            return f"✅ Web service is running and responding"
        else:
            agent_state["web_service_running"] = False
            
            # Log service not running
            # if CURRENT_BATTLE_ID: # Removed as per new_code
            #     log_battle_event( # Removed as per new_code
            #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
            #         message="Web service is not running", # Removed as per new_code
            #         reported_by="red_agent", # Removed as per new_code
            #         detail={"service_port": 80, "service_status": "stopped"} # Removed as per new_code
            #     ) # Removed as per new_code
            
            print(f"❌ Web service is not running")
            return f"❌ Web service is not running"
            
    except Exception as e:
        # Log service status check error
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Error checking service status: {str(e)}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"error": str(e), "service_port": 80} # Removed as per new_code
        #     ) # Removed as per new_code
        print(f"❌ Error checking service status: {str(e)}")
        return f"❌ Error checking service status: {str(e)}"


@ab.tool
def block_other_services() -> str:
    """Attempt to block other agents' web services."""
    try:
        if not agent_state["ssh_connected"]:
            return "❌ Not connected to battle arena. Connect first."
        
        # Log blocking attempt
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Attempting to block other services", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"blocking_type": "competitive_behavior"} # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"🛡️ Attempting to block other services")
        
        # Try to stop other services (this is competitive behavior)
        commands = [
            "pkill -f 'python.*service'",  # Kill other Python services
            "pkill -f 'http.server'",      # Kill HTTP servers
            "fuser -k 80/tcp 2>/dev/null || true"  # Kill anything on port 80
        ]
        
        results = []
        for command in commands:
            try:
                result = execute_ssh_command(command)
                results.append(f"Command '{command}': {result}")
            except Exception as e:
                results.append(f"Command '{command}' failed: {str(e)}")
        
        # Log blocking results
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Service blocking attempt completed", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={ # Removed as per new_code
        #             "commands_executed": len(commands), # Removed as per new_code
        #             "results": results # Removed as per new_code
        #         } # Removed as per new_code
        #     ) # Removed as per new_code
        
        return f"🛡️ Blocking attempt completed:\n" + "\n".join(results)
        
    except Exception as e:
        # Log blocking error
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Error blocking other services: {str(e)}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"error": str(e)} # Removed as per new_code
        #     ) # Removed as per new_code
        print(f"❌ Error blocking other services: {str(e)}")
        return f"❌ Error blocking other services: {str(e)}"


@ab.tool
def reset_agent_state() -> str:
    """Reset the agent's state and disconnect from SSH."""
    try:
        # Log state reset
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Resetting agent state", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={ # Removed as per new_code
        #             "ssh_connected": agent_state["ssh_connected"], # Removed as per new_code
        #             "web_service_running": agent_state["web_service_running"] # Removed as per new_code
        #         } # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"🔄 Resetting agent state")
        
        # Close SSH connection if open
        if agent_state["ssh_connected"] and agent_state["ssh_client"]:
            try:
                agent_state["ssh_client"].close()
            except Exception as e:
                print(f"⚠️ Error closing SSH connection: {str(e)}")
        
        # Reset state
        agent_state["ssh_connected"] = False
        agent_state["web_service_running"] = False
        agent_state["service_id"] = None
        agent_state["ssh_client"] = None
        agent_state["ssh_tools_added"] = False
        agent_state["ssh_credentials"] = None
        
        # Log state reset completion
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Agent state reset completed", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"ssh_connected": False, "web_service_running": False} # Removed as per new_code
        #     ) # Removed as per new_code
        
        print(f"✅ Agent state reset complete")
        return f"✅ Agent state reset complete"
        
    except Exception as e:
        # Log state reset error
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Error resetting agent state: {str(e)}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"error": str(e)} # Removed as per new_code
        #     ) # Removed as per new_code
        print(f"❌ Error resetting agent state: {str(e)}")
        return f"❌ Error resetting agent state: {str(e)}"


@ab.tool
def get_agent_status() -> str:
    """Get the current status of the red agent."""
    try:
        status = {
            "agent_id": agent_state["agent_id"],
            "ssh_connected": agent_state["ssh_connected"],
            "web_service_running": agent_state["web_service_running"],
            "service_id": agent_state["service_id"],
            "ssh_tools_added": agent_state["ssh_tools_added"],
            "battle_id": agent_state["battle_id"],
            "ssh_credentials": agent_state["ssh_credentials"] is not None
        }
        
        # Log status check
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message="Agent status requested", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail=status # Removed as per new_code
        #     ) # Removed as per new_code
        
        return f"📊 Red Agent Status: {json.dumps(status, indent=2)}"
        
    except Exception as e:
        # Log status check error
        # if CURRENT_BATTLE_ID: # Removed as per new_code
        #     log_battle_event( # Removed as per new_code
        #         battle_id=CURRENT_BATTLE_ID, # Removed as per new_code
        #         message=f"Error getting agent status: {str(e)}", # Removed as per new_code
        #         reported_by="red_agent", # Removed as per new_code
        #         detail={"error": str(e)} # Removed as per new_code
        #     ) # Removed as per new_code
        print(f"❌ Error getting agent status: {str(e)}")
        return f"❌ Error getting agent status: {str(e)}" 