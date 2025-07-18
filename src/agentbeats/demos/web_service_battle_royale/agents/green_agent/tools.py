# -*- coding: utf-8 -*-
"""
Battle Royale Green Agent Tools
This agent monitors the battle royale and determines the winner
by checking web services every 5 seconds for 2 minutes.
"""

import json
import time
import threading
import asyncio
import agentbeats as ab
from typing import Dict, Any

# Import SDK utilities
from agentbeats.utils.agents import send_message_to_agent, send_message_to_agents
from agentbeats.utils.environment import setup_container, cleanup_container
from agentbeats.utils.commands import SSHClient

# Agent state
agent_state = {
    "battle_environment_setup": False,
    "ssh_credentials": None,
    "agent_urls": [],
    "agent_ids": {},  # Map of agent_url -> random_id
    "monitoring_active": False,
    "monitoring_thread": None,
    "scores": {},
    "monitoring_results": [],
    "battle_id": None,
    "docker_container_running": False
}




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
        # set_battle_context(
        #     battle_id=battle_id,
        #     agent_name="green_agent",
        #     backend_url="http://localhost:9000",
        #     mcp_tools=mcp_tools
        # )
        
        # agent_state["battle_id"] = battle_id
        # agent_state["mcp_tools"] = mcp_tools
        
        # Log the setup completion
        # log_battle_event(
        #     battle_id=battle_id,
        #     message="Battle logging setup completed",
        #     reported_by="green_agent",
        #     detail={
        #         "mcp_tools_count": len(mcp_tools) if mcp_tools else 0,
        #         "setup_method": "with_mcp_tools"
        #     }
        # )
        
        print(f"🔧 Set up battle logging for battle {battle_id} with {len(mcp_tools) if mcp_tools else 0} MCP tools")
        return f"✅ Battle logging setup complete for battle {battle_id}"
    except Exception as e:
        return f"❌ Failed to setup battle logging: {str(e)}"


@ab.tool
def setup_battle_environment() -> str:
    """Set up the battle royale environment with Docker and SSH access."""
    try:
        # Log environment setup start
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message="Starting battle environment setup",
        #         reported_by="green_agent",
        #         detail={"setup_type": "docker_and_ssh"}
        #     )
        
        # Start Docker container using the dedicated function
        print(f"🐳 Setting up Docker container...")
        import asyncio
        docker_config = {"docker_dir": "arena", "compose_file": "docker-compose.yml"}
        docker_result = asyncio.run(setup_container(docker_config))
        print(f"🐳 Docker setup result: {docker_result}")
        
        if not docker_result:
            raise Exception(f"Docker container setup failed")
        
        agent_state["docker_container_running"] = True
        agent_state["battle_environment_setup"] = True
        
        # Generate SSH credentials
        agent_state["ssh_credentials"] = {
            "host": "localhost",
            "port": 2222,
            "username": "battle",
            "password": "battle123"
        }
        
        print(f"🔑 SSH credentials set: {agent_state['ssh_credentials']}")
        
        # Wait a moment for container to be ready
        import time
        time.sleep(3)
        
        print(f"🔑 SSH credentials configured and ready for battle")
        
        # Log environment setup completion
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message="Battle environment setup completed",
        #         reported_by="green_agent",
        #         detail={
        #             "ssh_host": agent_state["ssh_credentials"]["host"],
        #             "ssh_port": agent_state["ssh_credentials"]["port"],
        #             "ssh_username": agent_state["ssh_credentials"]["username"],
        #             "container_running": agent_state["docker_container_running"]
        #         }
        #     )
        
        return f"✅ Battle environment setup complete. Docker container running. SSH credentials: {agent_state['ssh_credentials']}"
    except Exception as e:
        # Log environment setup error
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message=f"Battle environment setup failed: {str(e)}",
        #         reported_by="green_agent",
        #         detail={"error": str(e)}
        #     )
        return f"❌ Failed to setup battle environment: {str(e)}"


@ab.tool
def start_battle_royale(battle_id: str, opponent_infos_json: str) -> str:
    """Start the battle royale competition between agents. This is the main entry point."""
    try:
        import uuid
        
        opponent_infos = json.loads(opponent_infos_json)
        
        agent_state["battle_id"] = battle_id
        agent_state["agent_urls"] = [opp["agent_url"] for opp in opponent_infos]
        
        # Generate random agent IDs for each opponent
        agent_state["agent_ids"] = {}
        agent_state["agent_url_to_opponent"] = {}  # Map agent URL to opponent info
        for opponent in opponent_infos:
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"  # Generate random 8-char ID
            agent_state["agent_ids"][opponent["agent_url"]] = agent_id
            agent_state["agent_url_to_opponent"][opponent["agent_url"]] = opponent
            print(f"🎯 Generated agent ID '{agent_id}' for {opponent['agent_url']} (opponent: {opponent.get('name', 'unknown')})")
        
        # Log battle start
        print(f"🚀 Starting battle royale {battle_id} with {len(opponent_infos)} opponents")
        # log_battle_event(
        #     battle_id=battle_id,
        #     message=f"Starting battle royale competition with {len(opponent_infos)} opponents",
        #     reported_by="green_agent",
        #     detail={
        #         "opponent_count": len(opponent_infos), 
        #         "opponent_urls": agent_state["agent_urls"],
        #         "agent_ids": agent_state["agent_ids"]
        #     }
        # )
        
        # Step 1: Setup battle environment (Docker + SSH)
        print(f"🔧 Setting up battle environment...")
        env_result = setup_battle_environment()
        print(f"🔧 Environment setup result: {env_result}")
        
        if not env_result.startswith("✅"):
            return f"❌ Failed to setup battle environment: {env_result}"
        
        # Send battle start message to all agents with their unique IDs
        import asyncio
        
        async def send_battle_info_to_agents():
            """Send battle information to all agents asynchronously."""
            try:
                # Create a generic battle message that includes all agent IDs
                agent_ids_info = "\n".join([f"- {url}: {agent_state['agent_ids'][url]}" for url in agent_state['agent_urls']])
                
                battle_message = f"""
BATTLE START - Battle Royale Competition

Battle ID: {battle_id}
SSH Credentials: {json.dumps(agent_state["ssh_credentials"])}

Instructions:
1. SSH into the battle arena using the provided credentials
2. Start a web service on port 80 inside the container
3. Serve your unique agent ID on the web service
4. Try to block other agents from taking over port 80
5. The agent with the highest uptime on port 80 wins

All Agent IDs:
{agent_ids_info}

Use the handle_battle_start() function to process this information.
"""
                
                # Log the broadcast message
                # if CURRENT_BATTLE_ID:
                #     log_battle_event(
                #         battle_id=CURRENT_BATTLE_ID,
                #         message=f"Broadcasting message to {len(agent_state['agent_urls'])} agents",
                #         reported_by="green_agent",
                #         detail={
                #             "target_urls": agent_state['agent_urls'],
                #             "message_length": len(battle_message),
                #             "message_preview": battle_message[:200] + "..." if len(battle_message) > 200 else battle_message
                #         }
                #     )
                
                # Send the same message to all agents concurrently
                print(f"📤 Sending battle info to {len(agent_state['agent_urls'])} agents...")
                responses = await send_message_to_agents(agent_state['agent_urls'], battle_message)
                
                # Log the broadcast results
                success_count = sum(1 for resp in responses.values() if not resp.startswith("Error:"))
                error_count = len(responses) - success_count
                
                # if CURRENT_BATTLE_ID:
                #     log_battle_event(
                #         battle_id=CURRENT_BATTLE_ID,
                #         message=f"Broadcast completed: {success_count} successful, {error_count} failed",
                #         reported_by="green_agent",
                #         detail={
                #             "total_agents": len(agent_state['agent_urls']),
                #             "successful_responses": success_count,
                #             "failed_responses": error_count,
                #             "responses": {url: resp[:100] + "..." if len(resp) > 100 else resp for url, resp in responses.items()}
                #         }
                #     )
                
                # Log the responses
                for agent_url, response in responses.items():
                    agent_id = agent_state["agent_ids"][agent_url]
                    print(f"📨 Response from {agent_url} (ID: {agent_id}): {response[:200]}...")
                    
                    # log_battle_event(
                    #     battle_id=battle_id,
                    #     message=f"Received response from {agent_url}",
                    #     reported_by="green_agent",
                    #     detail={
                    #         "target_agent": agent_url,
                    #         "agent_id": agent_id,
                    #         "response_preview": response[:200]
                    #     }
                    # )
                
                return f"✅ Sent battle info to {len(agent_state['agent_urls'])} agents"
                
            except Exception as e:
                error_msg = f"❌ Failed to send battle info to agents: {str(e)}"
                print(error_msg)
                # log_battle_event(
                #     battle_id=battle_id,
                #     message=f"Failed to send battle info to agents: {str(e)}",
                #     reported_by="green_agent",
                #     detail={"error": str(e)}
                # )
                return error_msg
        
        # Run the async function - use existing event loop if available
        try:
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                # If we're already in an event loop, use asyncio.create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, send_battle_info_to_agents())
                    send_result = future.result()
            except RuntimeError:
                # No event loop running, create a new one
                send_result = asyncio.run(send_battle_info_to_agents())
            
            print(f"📤 Battle info sending result: {send_result}")
        except Exception as e:
            print(f"❌ Error in async battle info sending: {str(e)}")
            # log_battle_event(
            #     battle_id=battle_id,
            #     message=f"Error in async battle info sending: {str(e)}",
            #     reported_by="green_agent",
            #     detail={"error": str(e)}
            # )
        
        # Verify Docker container is running and SSH credentials are set before starting monitoring
        if not agent_state["docker_container_running"]:
            print(f"⚠️ Docker container not running, attempting to start...")
            docker_config = {"docker_dir": "arena", "compose_file": "docker-compose.yml"}
            docker_result = asyncio.run(setup_container(docker_config))
            print(f"🐳 Docker start result: {docker_result}")
            
            if not docker_result:
                return f"❌ Failed to start Docker container"
        
        # Ensure SSH credentials are set
        if not agent_state["ssh_credentials"]:
            print(f"⚠️ SSH credentials not set, setting them up...")
            agent_state["ssh_credentials"] = {
                "host": "localhost",
                "port": 2222,
                "username": "battle",
                "password": "battle123"
            }
            print(f"🔑 SSH credentials set: {agent_state['ssh_credentials']}")
        
        # Start monitoring in background
        print(f"🔍 Starting monitoring thread...")
        start_monitoring_thread()
        
        # Log monitoring start
        # log_battle_event(
        #     battle_id=battle_id,
        #     message="Battle monitoring thread started",
        #     reported_by="green_agent",
        #     detail={"monitoring_duration_seconds": 50, "check_interval_seconds": 5}
        # )
        
        # Step 4: Wait for monitoring to complete and determine winner
        print(f"⏳ Waiting for battle monitoring to complete (50 seconds)...")
        
        # Wait for monitoring to finish
        while agent_state["monitoring_active"]:
            import time
            time.sleep(1)
        
        print(f"🏁 Battle monitoring completed. Determining winner...")
        
        # Step 5: Determine winner
        winner_result = determine_winner()
        print(f"🏆 Winner determination: {winner_result}")
        
        # Step 6: Generate battle summary
        summary_result = generate_battle_summary()
        print(f"📊 Battle summary: {summary_result}")
        
        # Step 7: Report final results
        # Always use the winner determination result, regardless of agent failures
        if "winner" in winner_result and "agent_" in winner_result:
            # Parse the winner from the JSON result instead of string parsing
            try:
                winner_data = json.loads(winner_result.split("Battle Result: ")[1])
                winner_name = winner_data["winner"]
                report_result = report_battle_result(winner_name, summary_result)
                print(f"📤 Battle report: {report_result}")
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                print(f"⚠️ Failed to parse winner from result: {e}")
                # Use the raw winner result as fallback
                report_result = report_battle_result(winner_result, summary_result)
                print(f"📤 Battle report (raw result): {report_result}")
        else:
            # Use the raw winner result
            report_result = report_battle_result(winner_result, summary_result)
            print(f"📤 Battle report (raw result): {report_result}")
        
        # Step 8: Cleanup
        cleanup_result = asyncio.run(cleanup_container("battle_royale", "arena"))
        print(f"🧹 Cleanup: {cleanup_result}")
        
        return f"✅ Battle royale completed successfully! Winner: {winner_result}. Summary: {summary_result}"
    except Exception as e:
        # Log battle start error
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message=f"Failed to start battle royale: {str(e)}",
        #         reported_by="green_agent",
        #         detail={"error": str(e)}
        #     )
        return f"❌ Failed to start battle royale: {str(e)}"


def start_monitoring_thread():
    """Start monitoring in a background thread."""
    if agent_state["monitoring_active"]:
        return
    
    agent_state["monitoring_active"] = True
    agent_state["monitoring_thread"] = threading.Thread(target=monitor_battle_progress, daemon=True)
    agent_state["monitoring_thread"].start()


def monitor_battle_progress():
    """Monitor the battle progress by checking web services every 5 seconds for 50 seconds."""
    try:
        print(f"🔍 Starting battle monitoring for battle {agent_state['battle_id']}")
        print(f"🔍 SSH credentials: {agent_state['ssh_credentials']}")
        print(f"🔍 Agent IDs: {agent_state['agent_ids']}")
        
        # log_battle_event(
        #     battle_id=agent_state['battle_id'],
        #     message="Starting battle monitoring (10 checks every 5 seconds)",
        #     reported_by="green_agent",
        #     detail={"total_checks": 10, "check_interval": 5}
        # )
        
        # Monitor for 50 seconds (10 checks at 5-second intervals)
        for i in range(10):
            if not agent_state["monitoring_active"]:
                print(f"🔍 Monitoring stopped early at check {i+1}")
                break
                
            print(f"📊 Monitoring check {i+1}/10 - Starting...")
            
            # Log each check start
            # log_battle_event(
            #     battle_id=agent_state['battle_id'],
            #     message=f"Monitoring check {i+1}/10 started",
            #     reported_by="green_agent",
            #     detail={"check_number": i+1, "total_checks": 10}
            # )
            
            # Check which agent is serving on port 8081 (mapped from container port 80)
            current_serving_agent = "NO_SERVICE"
            try:
                import subprocess
                import requests
                
                # Check port 8081 on the host (mapped from container port 80)
                print(f"🌐 Checking port 8081 (mapped from container port 80)...")
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:8081"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                print(f"🌐 Port 8081 check result: {result.returncode}")
                print(f"🌐 Port 8081 check stdout: {result.stdout}")
                if result.stderr:
                    print(f"🌐 Port 8081 check stderr: {result.stderr}")
                
                if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "NO_SERVICE":
                    # Service is running, check which agent ID is serving
                    service_content = result.stdout.strip()
                    print(f"🌐 Port 8081 response: '{service_content}'")
                    
                    # Find which agent ID is currently serving
                    serving_agent_id = None
                    for agent_url, agent_id in agent_state["agent_ids"].items():
                        if agent_id in service_content:
                            serving_agent_id = agent_id
                            current_serving_agent = agent_id
                            break
                    
                    if serving_agent_id:
                        # Update scores for the serving agent
                        if serving_agent_id not in agent_state["scores"]:
                            agent_state["scores"][serving_agent_id] = 0
                        agent_state["scores"][serving_agent_id] += 1
                        
                        print(f"✅ Agent '{serving_agent_id}' is serving on port 8081 (score: {agent_state['scores'][serving_agent_id]})")
                    else:
                        print(f"⚠️ Unknown service content: '{service_content}'")
                        current_serving_agent = f"UNKNOWN: {service_content[:50]}"
                else:
                    print(f"❌ No service running on port 8081")
                    current_serving_agent = "NO_SERVICE"
                    
            except subprocess.TimeoutExpired:
                print(f"❌ Timeout checking port 8081")
                current_serving_agent = "TIMEOUT"
            except Exception as e:
                print(f"❌ Error checking port 8081: {str(e)}")
                current_serving_agent = f"ERROR: {str(e)[:50]}"
            
            # Store monitoring result
            agent_state["monitoring_results"].append({
                "check": i + 1,
                "timestamp": time.time(),
                "scores": agent_state["scores"].copy(),
                "current_serving_agent": current_serving_agent
            })
            
            # Log monitoring progress for EVERY check with detailed information
            # log_battle_event(
            #     battle_id=agent_state['battle_id'],
            #     message=f"Monitoring check {i+1}/10 completed",
            #     reported_by="green_agent",
            #     detail={
            #         "check_number": i+1, 
            #         "total_checks": 10,
            #         "current_serving_agent": current_serving_agent,
            #         "current_scores": agent_state["scores"].copy(),
            #         "all_agent_ids": list(agent_state["agent_ids"].values())
            #     }
            # )
            
            print(f"📊 Monitoring check {i+1}/10 - Completed. Waiting 5 seconds...")
            time.sleep(5)  # Wait 5 seconds between checks
            print(f"📊 Monitoring check {i+1}/10 - 5 seconds elapsed, continuing...")
        
        # Battle finished
        print(f"🏁 Battle monitoring loop completed - all 10 checks done")
        agent_state["monitoring_active"] = False
        print(f"🏁 Battle monitoring completed for {agent_state['battle_id']}")
        # log_battle_event(
        #     battle_id=agent_state['battle_id'],
        #     message="Battle monitoring completed - waiting for manual winner determination",
        #     reported_by="green_agent",
        #     detail={"final_scores": agent_state["scores"], "total_checks": 10}
        # )
        
        print("🏁 Battle monitoring completed. Use 'determine_winner()' to announce the results when ready.")
        
        # Clean up Docker container after battle
        print(f"🧹 Cleaning up Docker container...")
        try:
            cleanup_result = asyncio.run(cleanup_container("battle_royale", "arena"))
            print(f"🧹 Cleanup result: {cleanup_result}")
        except Exception as e:
            print(f"⚠️ Failed to clean up Docker container: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error in monitoring thread: {str(e)}")
        # log_battle_event(
        #     battle_id=agent_state['battle_id'],
        #     message=f"Error in monitoring thread: {str(e)}",
        #     reported_by="green_agent",
        #     detail={"error": str(e)}
        # )
        agent_state["monitoring_active"] = False


# @ab.tool
# def stop_docker_container() -> str:
    """Stop and remove the Docker container."""
    try:
        import subprocess
        import os
        
        # Use the correct absolute path to the arena directory
        docker_dir = "/Users/danielmiao/agentbeats/scenarios/battle_royale/arena"
        
        print(f"🐳 Stopping Docker container from {docker_dir}")
        
        # Check if the directory exists
        if not os.path.exists(docker_dir):
            return f"❌ Arena directory not found: {docker_dir}"
        
        # Stop and remove all Docker containers
        result = subprocess.run(
            ["docker-compose", "down", "--remove-orphans"],
            cwd=docker_dir,
            capture_output=True,
            text=True
        )
        
        # Also force remove containers if they still exist
        containers_to_remove = ["battle-royale-arena", "battle-dev-monitor"]
        for container_name in containers_to_remove:
            force_remove_result = subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True
            )
            print(f"🐳 Force remove {container_name} result: {force_remove_result.returncode}")
        
        if result.returncode == 0:
            agent_state["docker_container_running"] = False
            return f"✅ Docker container stopped and removed from {docker_dir}"
        else:
            return f"❌ Failed to stop Docker container: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error stopping Docker container: {str(e)}"


# @ab.tool
# def start_docker_container() -> str:
    """Manually start the Docker container."""
    try:
        import subprocess
        import os
        
        # Use the correct absolute path to the arena directory
        docker_dir = "/Users/danielmiao/agentbeats/scenarios/battle_royale/arena"
        
        print(f"🐳 Starting Docker container from {docker_dir}")
        
        # Check if the directory exists
        if not os.path.exists(docker_dir):
            return f"❌ Arena directory not found: {docker_dir}"
        
        # First, stop and remove any existing containers
        print(f"🐳 Stopping and removing any existing containers...")
        stop_result = subprocess.run(
            ["docker-compose", "down", "--remove-orphans"],
            cwd=docker_dir,
            capture_output=True,
            text=True
        )
        print(f"🐳 Stop result: {stop_result.returncode}")
        
        # Force remove all related containers if they exist
        containers_to_remove = ["battle-royale-arena", "battle-dev-monitor"]
        for container_name in containers_to_remove:
            force_remove_result = subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True
            )
            print(f"🐳 Force remove {container_name} result: {force_remove_result.returncode}")
            if force_remove_result.stderr:
                print(f"🐳 {container_name} remove stderr: {force_remove_result.stderr}")
        
        # Start the Docker container
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=docker_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            agent_state["docker_container_running"] = True
            return f"✅ Docker container started successfully from {docker_dir}"
        else:
            return f"❌ Failed to start Docker container: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error starting Docker container: {str(e)}"


# @ab.tool
# def cleanup_all_containers() -> str:
    """Force clean up all battle royale containers and networks."""
    try:
        import subprocess
        
        # Stop and remove all containers
        containers_to_remove = ["battle-royale-arena", "battle-dev-monitor"]
        results = []
        
        for container_name in containers_to_remove:
            # Force remove container
            result = subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True
            )
            results.append(f"{container_name}: {result.returncode}")
            print(f"🐳 Force remove {container_name} result: {result.returncode}")
        
        # Remove the network
        network_result = subprocess.run(
            ["docker", "network", "rm", "arena_battle-network"],
            capture_output=True,
            text=True
        )
        results.append(f"network: {network_result.returncode}")
        print(f"🐳 Remove network result: {network_result.returncode}")
        
        # Reset state
        agent_state["docker_container_running"] = False
        
        return f"✅ Cleanup completed: {', '.join(results)}"
    except Exception as e:
        return f"❌ Error cleaning up containers: {str(e)}"


@ab.tool
def set_ssh_credentials() -> str:
    """Set SSH credentials for the battle arena."""
    try:
        agent_state["ssh_credentials"] = {
            "host": "localhost",
            "port": 2222,
            "username": "battle",
            "password": "battle123"
        }
        
        print(f"🔑 SSH credentials set: {agent_state['ssh_credentials']}")
        
        # Log the credential setup
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message="SSH credentials set manually",
        #         reported_by="green_agent",
        #         detail={"ssh_credentials": agent_state["ssh_credentials"]}
        #     )
        
        return f"✅ SSH credentials set: {agent_state['ssh_credentials']}"
    except Exception as e:
        return f"❌ Error setting SSH credentials: {str(e)}"


@ab.tool
def test_ssh_connection() -> str:
    """Test SSH connection to the Docker container."""
    try:
        if not agent_state["ssh_credentials"]:
            return "❌ SSH credentials not set"
        
        import subprocess
        
        ssh_test_cmd = [
            "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", 
            f"{agent_state['ssh_credentials']['username']}@{agent_state['ssh_credentials']['host']}", 
            "-p", str(agent_state['ssh_credentials']['port']), "echo 'SSH connection successful'"
        ]
        
        print(f"🔌 Testing SSH: {' '.join(ssh_test_cmd)}")
        
        result = subprocess.run(
            ssh_test_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"✅ SSH connection successful: {result.stdout.strip()}"
        else:
            return f"❌ SSH connection failed: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error testing SSH: {str(e)}"


@ab.tool
def cleanup_battle_environment() -> str:
    """Clean up the battle environment (stop Docker container)."""
    try:
        if agent_state["docker_container_running"]:
            import asyncio
            cleanup_result = asyncio.run(cleanup_container("battle_royale", "arena"))
            return f"🧹 Battle environment cleaned up: {cleanup_result}"
        else:
            return "🧹 No Docker container running to clean up"
    except Exception as e:
        return f"❌ Error cleaning up battle environment: {str(e)}"


@ab.tool
def check_docker_status() -> str:
    """Check if the Docker container is running."""
    try:
        import subprocess
        
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=battle-royale-arena", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if "battle-royale-arena" in result.stdout:
            return "✅ Docker container 'battle-royale-arena' is running"
        else:
            return "❌ Docker container 'battle-royale-arena' is not running"
            
    except Exception as e:
        return f"❌ Error checking Docker status: {str(e)}"


@ab.tool
def get_battle_status() -> str:
    """Get the current status of the battle royale."""
    try:
        if not agent_state["battle_id"]:
            return "❌ No battle in progress"
        
        status = {
            "battle_id": agent_state["battle_id"],
            "monitoring_active": agent_state["monitoring_active"],
            "current_scores": agent_state["scores"],
            "total_checks": len(agent_state["monitoring_results"]),
            "environment_setup": agent_state["battle_environment_setup"]
        }
        
        # Log status check
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message="Battle status requested",
        #         reported_by="green_agent",
        #         detail={
        #             "monitoring_active": agent_state["monitoring_active"],
        #             "total_checks": len(agent_state["monitoring_results"]),
        #             "current_scores": agent_state["scores"]
        #         }
        #     )
        
        return f"📊 Battle Status: {json.dumps(status, indent=2)}"
    except Exception as e:
        # Log status check error
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message=f"Error getting battle status: {str(e)}",
        #         reported_by="green_agent",
        #         detail={"error": str(e)}
        #     )
        return f"❌ Error getting battle status: {str(e)}"


@ab.tool
def determine_winner() -> str:
    """Determine the winner of the battle royale based on uptime scores."""
    try:
        # Check if battle monitoring has completed (10 checks over 50 seconds)
        total_checks = len(agent_state["monitoring_results"])
        required_checks = 10
        
        # Check if battle monitoring has completed (10 checks over 50 seconds)
        if total_checks < required_checks:
            remaining_checks = required_checks - total_checks
            remaining_time = remaining_checks * 5  # 5 seconds per check
            return f"❌ Battle monitoring not complete. {total_checks}/{required_checks} checks done. {remaining_checks} checks remaining ({remaining_time} seconds)."
        
        if agent_state["monitoring_active"]:
            return "❌ Battle monitoring is still active. Wait for monitoring to complete before determining winner."
        
        # If no agents have scores after the full monitoring period, report a draw
        if not agent_state["scores"]:
            print("⚠️ No agents have scores after full monitoring period - all agents failed to create services")
            # Create a draw result
            result = {
                "winner": "draw",
                "winner_score": 0,
                "total_checks": total_checks,
                "required_checks": required_checks,
                "uptime_percentages": {},
                "all_scores": {},
                "reason": "All agents failed to create services during full battle period"
            }
            
            announcement = f"""The battle has concluded after the full 50-second monitoring period. All agents failed to create web services during the battle. The battle ran for the complete duration with {total_checks} monitoring checks, but no agent was able to maintain a service on port 80."""
            
            print(f"📢 {announcement}")
            
            # Log the draw result
            # if CURRENT_BATTLE_ID:
            #     log_battle_event(
            #         battle_id=CURRENT_BATTLE_ID,
            #         message=announcement,
            #         reported_by="green_agent",
            #         detail={
            #             "winner": "draw",
            #             "total_checks": total_checks,
            #             "required_checks": required_checks,
            #             "reason": "All agents failed to create services during full battle period",
            #             "battle_duration_seconds": 50,
            #             "check_interval_seconds": 5
            #         }
            #     )
            
            return f"🏆 Battle Result: {json.dumps(result, indent=2)}"
        
        # Log winner determination start
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message="Starting winner determination",
        #         reported_by="green_agent",
        #         detail={"current_scores": agent_state["scores"], "total_checks": total_checks}
        #     )
        
        # Find agent with highest score
        winner = max(agent_state["scores"].items(), key=lambda x: x[1])
        winner_agent_id, winner_score = winner
        
        # Map agent ID back to agent URL
        winner_agent_url = None
        for agent_url, agent_id in agent_state["agent_ids"].items():
            if agent_id == winner_agent_id:
                winner_agent_url = agent_url
                break
        
        # Map agent URL to opponent name for backend reporting
        winner_name = winner_agent_id  # fallback to agent ID
        if winner_agent_url and winner_agent_url in agent_state.get("agent_url_to_opponent", {}):
            opponent_info = agent_state["agent_url_to_opponent"][winner_agent_url]
            winner_name = opponent_info.get("name", winner_agent_id)  # Use opponent name for backend
            print(f"🏆 Winner mapped: {winner_agent_url} -> {winner_name} (opponent name)")
        else:
            print(f"🏆 Winner fallback: using agent ID {winner_agent_id}")
        
        # Calculate uptime percentages based on completed monitoring period
        uptime_percentages = {}
        for agent_id, score in agent_state["scores"].items():
            # Map agent ID to agent URL for display
            agent_url = None
            for url, aid in agent_state["agent_ids"].items():
                if aid == agent_id:
                    agent_url = url
                    break
            # Use opponent name for display if available
            display_name = agent_id  # fallback
            if agent_url and agent_url in agent_state.get("agent_url_to_opponent", {}):
                opponent_info = agent_state["agent_url_to_opponent"][agent_url]
                display_name = opponent_info.get("name", agent_id)
            uptime_percentages[display_name] = (score / required_checks) * 100
        
        result = {
            "winner": winner_name,
            "winner_score": winner_score,
            "total_checks": total_checks,
            "required_checks": required_checks,
            "uptime_percentages": uptime_percentages,
            "all_scores": agent_state["scores"]
        }
        
        # Take a moment to think and analyze the results
        print("🤔 Analyzing battle results...")
        time.sleep(2)  # Brief pause for dramatic effect
        
        print(f"🏆 Winner determined: {winner_name} with {winner_score}/{required_checks} checks ({uptime_percentages[winner_name]:.1f}% uptime)")
        
        # Create detailed announcement message
        announcement = f"""The battle has concluded successfully! The agent "{winner_name}" maintained {uptime_percentages[winner_name]:.1f}% uptime throughout the battle, achieving a score of {winner_score}/{total_checks} checks. The battle ran for the full 50 seconds with checks every 5 seconds, and all monitoring completed as expected. The winner has been determined and the results have been reported to the system."""
        
        print(f"📢 {announcement}")
        
        # Log winner determination with detailed announcement
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message=announcement,
        #         reported_by="green_agent",
        #         detail={
        #             "winner": winner_name,
        #             "winner_score": winner_score,
        #             "winner_uptime_percentage": uptime_percentages[winner_name],
        #             "total_checks": total_checks,
        #             "required_checks": required_checks,
        #             "all_uptime_percentages": uptime_percentages,
        #             "battle_duration_seconds": 50,
        #             "check_interval_seconds": 5
        #         }
        #     )
        
        return f"🏆 Battle Result: {json.dumps(result, indent=2)}"
    except Exception as e:
        # Log winner determination error
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message=f"Error determining winner: {str(e)}",
        #         reported_by="green_agent",
        #         detail={"error": str(e)}
        #     )
        return f"❌ Error determining winner: {str(e)}"


@ab.tool
def generate_battle_summary() -> str:
    """Generate a comprehensive summary of the battle royale."""
    try:
        if not agent_state["battle_id"]:
            return "❌ No battle data available for summary"
        
        # Check if battle monitoring has completed
        total_checks = len(agent_state["monitoring_results"])
        required_checks = 10
        
        if total_checks < required_checks:
            remaining_checks = required_checks - total_checks
            remaining_time = remaining_checks * 5  # 5 seconds per check
            return f"❌ Battle monitoring not complete. {total_checks}/{required_checks} checks done. {remaining_checks} checks remaining ({remaining_time} seconds). Cannot generate summary yet."
        
        if agent_state["monitoring_active"]:
            return "❌ Battle monitoring is still active. Wait for monitoring to complete before generating summary."
        
        # Log summary generation start
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message="Starting battle summary generation",
        #         reported_by="green_agent"
        #     )
        
        # Get winner info
        winner_result = determine_winner()
        if winner_result.startswith("❌"):
            return winner_result
        
        # Parse winner info
        winner_data = json.loads(winner_result.split("Battle Result: ")[1])
        
        summary = {
            "battle_id": agent_state["battle_id"],
            "duration_seconds": 50,
            "monitoring_interval_seconds": 5,
            "total_checks": winner_data["total_checks"],
            "winner": winner_data["winner"],
            "winner_uptime_percentage": winner_data["uptime_percentages"][winner_data["winner"]],
            "all_uptime_percentages": winner_data["uptime_percentages"],
            "environment_setup": agent_state["battle_environment_setup"],
            "ssh_credentials_provided": agent_state["ssh_credentials"] is not None,
            "opponent_count": len(agent_state["agent_urls"])
        }
        
        # Log summary generation completion
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message="Battle summary generated",
        #         reported_by="green_agent",
        #         detail={
        #             "winner": winner_data["winner"],
        #             "total_checks": winner_data["total_checks"],
        #             "opponent_count": len(agent_state["agent_urls"])
        #         }
        #     )
        
        return f"📋 Battle Summary: {json.dumps(summary, indent=2)}"
    except Exception as e:
        # Log summary generation error
        # if CURRENT_BATTLE_ID:
        #     log_battle_event(
        #         battle_id=CURRENT_BATTLE_ID,
        #         message=f"Error generating battle summary: {str(e)}",
        #         reported_by="green_agent",
        #         detail={"error": str(e)}
        #     )
        return f"❌ Error generating battle summary: {str(e)}"


@ab.tool
def report_battle_result(winner: str, summary: str = "") -> str:
    """Report the final battle result using the SDK logging utilities."""
    try:
        # from agentbeats.utils.logging import CURRENT_BACKEND_URL
        
        # Use battle_id from agent_state if CURRENT_BATTLE_ID is not available
        battle_id = agent_state.get("battle_id")
        
        if not battle_id:
            return "❌ No battle context set. Cannot report result."
        
        # Log the winner announcement
        # log_battle_event(
        #     battle_id=battle_id,
        #     message=f"Announcing battle winner: {winner}",
        #     reported_by="green_agent",
        #     detail={"winner": winner, "summary_length": len(summary)}
        # )
        
        # Report the final result
        detail = {
            "summary": summary,
            "battle_type": "battle_royale",
            "monitoring_duration_seconds": 50,
            "check_interval_seconds": 5
        }
        
        # log_battle_result(
        #     battle_id=battle_id,
        #     message=f"Battle Royale completed - {winner} wins",
        #     winner=winner,
        #     detail=detail,
        #     backend_url=CURRENT_BACKEND_URL
        # )
        
        return f"✅ Battle result reported: {winner} wins"
    except Exception as e:
        return f"❌ Failed to report battle result: {str(e)}" 