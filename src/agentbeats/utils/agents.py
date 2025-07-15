# -*- coding: utf-8 -*-
"""
Agent communication utilities for AgentBeats scenarios.
"""

import httpx
import asyncio
from typing import Optional, List, Dict, Any
from uuid import uuid4

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    AgentCard, Message, Part, TextPart, Role, 
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    MessageSendParams,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)
from .logging import log_battle_event, CURRENT_BATTLE_ID, CURRENT_AGENT_NAME, CURRENT_BACKEND_URL
async def create_a2a_client(target_url: str) -> A2AClient:
    """
    Create an A2A client for communicating with an agent at *target_url*.
    """
    httpx_client = httpx.AsyncClient()
    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=target_url)
    card: AgentCard | None = await resolver.get_agent_card(
        relative_card_path="/.well-known/agent.json"
    )
    if card is None:
        raise RuntimeError(f"Failed to resolve agent card from {target_url}")

    return A2AClient(httpx_client=httpx_client, agent_card=card)


async def send_message_to_agent(target_url: str, message: str) -> str:
    """
    Forward *message* to another A2A agent at *target_url* and stream back
    the plain-text response.
    """
    
    # Log the message being sent
    if CURRENT_BATTLE_ID:
        log_battle_event(
            battle_id=CURRENT_BATTLE_ID,
            message=f"Sending message to agent at {target_url}",
            reported_by=CURRENT_AGENT_NAME or "system",
            detail={
                "target_url": target_url,
                "message_length": len(message),
                "message_preview": message[:200] + "..." if len(message) > 200 else message
            },
            backend_url=CURRENT_BACKEND_URL
        )
    
    client = await create_a2a_client(target_url)

    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=message))],
            messageId=uuid4().hex,
            taskId=uuid4().hex,
        )
    )
    req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
    chunks: List[str] = []

    async for chunk in client.send_message_streaming(req):
        if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
            continue
        event = chunk.root.result
        if isinstance(event, TaskArtifactUpdateEvent):
            for p in event.artifact.parts:
                if isinstance(p.root, TextPart):
                    chunks.append(p.root.text)
        elif isinstance(event, TaskStatusUpdateEvent):
            msg = event.status.message
            if msg:
                for p in msg.parts:
                    if isinstance(p.root, TextPart):
                        chunks.append(p.root.text)

    response = "".join(chunks).strip() or "No response from agent."
    
    # Log the response received
    if CURRENT_BATTLE_ID:
        log_battle_event(
            battle_id=CURRENT_BATTLE_ID,
            message=f"Received response from agent at {target_url}",
            reported_by=CURRENT_AGENT_NAME or "system",
            detail={
                "target_url": target_url,
                "response_length": len(response),
                "response_preview": response[:200] + "..." if len(response) > 200 else response
            },
            backend_url=CURRENT_BACKEND_URL
        )
    
    return response


async def send_message_to_agents(target_urls: List[str], message: str) -> Dict[str, str]:
    """
    Forward *message* to multiple A2A agents at *target_urls* concurrently and stream back
    the plain-text responses.
    """
    
    # Log the broadcast message
    if CURRENT_BATTLE_ID:
        log_battle_event(
            battle_id=CURRENT_BATTLE_ID,
            message=f"Broadcasting message to {len(target_urls)} agents",
            reported_by=CURRENT_AGENT_NAME or "system",
            detail={
                "target_urls": target_urls,
                "message_length": len(message),
                "message_preview": message[:200] + "..." if len(message) > 200 else message
            },
            backend_url=CURRENT_BACKEND_URL
        )
    
    async def send_to_single_agent(url: str) -> tuple[str, str]:
        try:
            response = await send_message_to_agent(url, message)
            return url, response
        except Exception as e:
            return url, f"Error: {str(e)}"
    
    # Create tasks for all agents
    tasks = [send_to_single_agent(url) for url in target_urls]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    response_dict = {}
    success_count = 0
    error_count = 0
    
    for i, result in enumerate(results):
        url = target_urls[i]
        if isinstance(result, Exception):
            response_dict[url] = f"Error: {str(result)}"
            error_count += 1
        elif isinstance(result, tuple) and len(result) == 2:
            response_dict[url] = result[1]  # result is (url, response) tuple
            success_count += 1
        else:
            response_dict[url] = f"Unexpected result format: {type(result)}"
            error_count += 1
    
    # Log the broadcast results
    if CURRENT_BATTLE_ID:
        log_battle_event(
            battle_id=CURRENT_BATTLE_ID,
            message=f"Broadcast completed: {success_count} successful, {error_count} failed",
            reported_by=CURRENT_AGENT_NAME or "system",
            detail={
                "total_agents": len(target_urls),
                "successful_responses": success_count,
                "failed_responses": error_count,
                "responses": {url: resp[:100] + "..." if len(resp) > 100 else resp for url, resp in response_dict.items()}
            },
            backend_url=CURRENT_BACKEND_URL
        )
    
    return response_dict


async def check_agent_health(target_url: str) -> bool:
    """
    Check if an agent is healthy and responding.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{target_url}/.well-known/agent.json", timeout=5)
            return response.status_code == 200
    except Exception:
        return False


async def ping_agents(agent_urls: List[str]) -> Dict[str, bool]:
    """
    Check health of multiple agents concurrently.
    
    Args:
        agent_urls: List of agent URLs to check
        
    Returns:
        Dictionary mapping agent URLs to their health status
    """
    async def ping_single_agent(url: str) -> tuple[str, bool]:
        is_healthy = await check_agent_health(url)
        return url, is_healthy
    
    # Create tasks for all agents
    tasks = [ping_single_agent(url) for url in agent_urls]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    health_dict = {}
    for i, result in enumerate(results):
        url = agent_urls[i]
        if isinstance(result, Exception):
            health_dict[url] = False
        elif isinstance(result, tuple) and len(result) == 2:
            health_dict[url] = result[1]  # result is (url, health_status) tuple
        else:
            health_dict[url] = False
    
    return health_dict 