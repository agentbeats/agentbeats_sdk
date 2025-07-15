# -*- coding: utf-8 -*-
"""
Environment and infrastructure utilities for AgentBeats scenarios.
"""

import subprocess
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

import agentbeats as ab
from .logging import auto_log


@auto_log(action_name="Docker Environment Setup")
async def setup_docker_environment(config: Dict[str, Any]) -> bool:
    """
    Set up a Docker environment for a scenario.
    
    Args:
        config: Configuration dictionary with docker settings
        
    Returns:
        True if successful, False otherwise
    """
    from .logging import log_battle_event, CURRENT_BATTLE_ID, CURRENT_AGENT_NAME, CURRENT_BACKEND_URL
    
    try:
        docker_dir = config.get("docker_dir", "docker")
        compose_file = config.get("compose_file", "docker-compose.yml")
        
        # Log setup attempt
        if CURRENT_BATTLE_ID:
            log_battle_event(
                battle_id=CURRENT_BATTLE_ID,
                message=f"Setting up Docker environment with config: {docker_dir}/{compose_file}",
                reported_by=CURRENT_AGENT_NAME or "system",
                detail={
                    "docker_dir": docker_dir,
                    "compose_file": compose_file,
                    "config": config
                },
                backend_url=CURRENT_BACKEND_URL
            )
        
        # Change to docker directory
        docker_path = Path(docker_dir)
        if not docker_path.exists():
            error_msg = f"Docker directory not found: {docker_dir}"
            if CURRENT_BATTLE_ID:
                from .logging import log_error
                log_error(
                    battle_id=CURRENT_BATTLE_ID,
                    error_message=error_msg,
                    error_type="error",
                    reported_by=CURRENT_AGENT_NAME or "system",
                    backend_url=CURRENT_BACKEND_URL
                )
            print(f"❌ {error_msg}")
            return False
        
        # Stop any existing containers
        if CURRENT_BATTLE_ID:
            log_battle_event(
                battle_id=CURRENT_BATTLE_ID,
                message="Stopping existing Docker containers",
                reported_by=CURRENT_AGENT_NAME or "system",
                detail={"command": "docker-compose down"},
                backend_url=CURRENT_BACKEND_URL
            )
        
        print("🔄 Stopping existing containers...")
        down_result = subprocess.run(["docker-compose", "down"], cwd=docker_path, capture_output=True, text=True)
        
        if CURRENT_BATTLE_ID:
            log_battle_event(
                battle_id=CURRENT_BATTLE_ID,
                message=f"Docker down completed with exit code {down_result.returncode}",
                reported_by=CURRENT_AGENT_NAME or "system",
                detail={
                    "command": "docker-compose down",
                    "exit_code": down_result.returncode,
                    "stdout": down_result.stdout,
                    "stderr": down_result.stderr
                },
                backend_url=CURRENT_BACKEND_URL
            )
        
        # Start the environment
        if CURRENT_BATTLE_ID:
            log_battle_event(
                battle_id=CURRENT_BATTLE_ID,
                message="Starting Docker environment with docker-compose up",
                reported_by=CURRENT_AGENT_NAME or "system",
                detail={"command": "docker-compose up -d --build"},
                backend_url=CURRENT_BACKEND_URL
            )
        
        print("🚀 Starting Docker environment...")
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"], 
            cwd=docker_path,
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            success_msg = "Docker environment started successfully"
            if CURRENT_BATTLE_ID:
                log_battle_event(
                    battle_id=CURRENT_BATTLE_ID,
                    message=success_msg,
                    reported_by=CURRENT_AGENT_NAME or "system",
                    detail={
                        "command": "docker-compose up -d --build",
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "containers_started": True
                    },
                    backend_url=CURRENT_BACKEND_URL
                )
            print(f"✅ {success_msg}")
            return True
        else:
            error_msg = f"Failed to start Docker environment: {result.stderr}"
            if CURRENT_BATTLE_ID:
                from .logging import log_error
                log_error(
                    battle_id=CURRENT_BATTLE_ID,
                    error_message=error_msg,
                    error_type="error",
                    reported_by=CURRENT_AGENT_NAME or "system",
                    backend_url=CURRENT_BACKEND_URL
                )
            print(f"❌ {error_msg}")
            return False
            
    except Exception as e:
        error_msg = f"Error setting up Docker environment: {str(e)}"
        if CURRENT_BATTLE_ID:
            from .logging import log_error
            log_error(
                battle_id=CURRENT_BATTLE_ID,
                error_message=error_msg,
                error_type="error",
                reported_by=CURRENT_AGENT_NAME or "system",
                backend_url=CURRENT_BACKEND_URL
            )
        print(f"❌ {error_msg}")
        return False


@auto_log(action_name="Docker Environment Cleanup")
async def cleanup_docker_environment(env_id: str) -> bool:
    """
    Clean up a Docker environment.
    
    Args:
        env_id: Environment identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Stop and remove containers
        result = subprocess.run(
            ["docker-compose", "down", "--volumes", "--remove-orphans"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Docker environment {env_id} cleaned up successfully")
            return True
        else:
            print(f"❌ Failed to cleanup Docker environment: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error cleaning up Docker environment: {str(e)}")
        return False


@auto_log(action_name="Container Health Check")
async def check_container_health(container_name: str) -> bool:
    """
    Check if a Docker container is healthy and running.
    
    Args:
        container_name: Name of the container to check
        
    Returns:
        True if container is healthy, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            status = result.stdout.strip()
            return "Up" in status and "healthy" in status.lower()
        else:
            return False
            
    except Exception:
        return False 