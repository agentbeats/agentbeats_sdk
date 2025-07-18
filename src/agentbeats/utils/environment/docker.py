# -*- coding: utf-8 -*-
"""
Environmental utilities for easier development using the Agentbeats SDK.
"""

import subprocess
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path


async def setup_container(config: Dict[str, Any]) -> bool:
    """Set up container environment."""
    
    try:
        docker_dir = config.get("docker_dir", "docker")
        compose_file = config.get("compose_file", "docker-compose.yml")
        
        # Change to docker directory
        docker_path = Path(docker_dir)
        if not docker_path.exists():
            print(f"Error: Docker directory not found: {docker_dir}")
            return False
        
        # Stop any existing containers
        print("Stopping existing containers...")
        down_result = subprocess.run(["docker-compose", "down"], cwd=docker_path, capture_output=True, text=True)
        
        # Start the environment
        print("Starting Docker environment...")
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"], 
            cwd=docker_path,
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("Docker environment started successfully")
            return True
        else:
            print(f"Failed to start Docker environment: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error setting up Docker environment: {str(e)}")
        return False


async def cleanup_container(env_id: str) -> bool:
    """Destroy and reset container environment."""
    try:
        # Stop and remove containers
        result = subprocess.run(
            ["docker-compose", "down", "--volumes", "--remove-orphans"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Docker environment {env_id} cleaned up successfully")
            return True
        else:
            print(f"Failed to cleanup Docker environment: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error cleaning up Docker environment: {str(e)}")
        return False


async def check_container_health(container_name: str) -> bool:
    """Check container health."""
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