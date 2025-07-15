# -*- coding: utf-8 -*-
"""
Common utility functions for AgentBeats scenarios.
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

    return "".join(chunks).strip() or "No response from agent."


async def send_message_to_agents(target_urls: List[str], message: str) -> Dict[str, str]:
    """
    Forward *message* to multiple A2A agents at *target_urls* concurrently and stream back
    the plain-text responses.
    """
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
    for i, result in enumerate(results):
        url = target_urls[i]
        if isinstance(result, Exception):
            response_dict[url] = f"Error: {str(result)}"
        elif isinstance(result, tuple) and len(result) == 2:
            response_dict[url] = result[1]  # result is (url, response) tuple
        else:
            response_dict[url] = f"Unexpected result format: {type(result)}"
    
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