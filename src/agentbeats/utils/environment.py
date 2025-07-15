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


async def setup_docker_environment(config: Dict[str, Any]) -> bool:
    """
    Set up a Docker environment for a scenario.
    
    Args:
        config: Configuration dictionary with docker settings
        
    Returns:
        True if successful, False otherwise
    """
    try:
        docker_dir = config.get("docker_dir", "docker")
        compose_file = config.get("compose_file", "docker-compose.yml")
        
        # Change to docker directory
        docker_path = Path(docker_dir)
        if not docker_path.exists():
            print(f"❌ Docker directory not found: {docker_dir}")
            return False
        
        # Stop any existing containers
        print("🔄 Stopping existing containers...")
        subprocess.run(["docker-compose", "down"], cwd=docker_path, capture_output=True)
        
        # Start the environment
        print("🚀 Starting Docker environment...")
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"], 
            cwd=docker_path,
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Docker environment started successfully")
            return True
        else:
            print(f"❌ Failed to start Docker environment: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up Docker environment: {str(e)}")
        return False


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