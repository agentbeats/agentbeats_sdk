# -*- coding: utf-8 -*-

"""
AgentBeats SDK implementation for the AgentBeats platform.
"""

import tomllib
import uvicorn
import os
from typing import Dict, List, Any, Optional, Callable

from agents import (
    Agent, 
    Runner, 
    function_tool, 
    Model, 
    ModelProvider, 
    OpenAIChatCompletionsModel, 
    set_tracing_disabled
)
from agents.mcp import MCPServerSse
from openai import AsyncOpenAI

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import TaskUpdater, InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.events import EventQueue
from a2a.utils import new_task, new_agent_text_message
from a2a.types import Part, TextPart, TaskState, AgentCard

__all__ = [
    "BeatsAgent",
    "AgentBeatsExecutor",
]


def create_agent(
        agent_name: str,
        instructions: str,
        model_type: str, 
        model_name: str,
        tools: Optional[List[Any]] = None,
        mcp_servers: Optional[List[MCPServerSse]] = None) -> Agent:
    """Create an Agent instance based on the model type and name."""

    agent_args = {
        "name": agent_name,
        "instructions": instructions,
        "tools": tools or [],
        "mcp_servers": mcp_servers or [],
    }

    # openai agents, e.g. "o4-mini"
    if model_type == "openai":
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY").strip() # in case of empty \n
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        
        print("[AgentBeats] Using OpenAI model:", model_name)
        return Agent(**agent_args, model=model_name)
        
    # openrouter agents, e.g. "anthropic/claude-3.5-sonnet"
    elif model_type == "openrouter":
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY").strip() # in case of empty \n
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set")
        
        print("[AgentBeats] Using OpenRouter model:", model_name)
        set_tracing_disabled(True)  # Disable tracing for OpenRouter models
        os.environ["OPENAI_TRACING_V2"] = "false"
        openrouter_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", 
                                        api_key=OPENROUTER_API_KEY)
        openrouter_model_provider = OpenRouterModelProvider()
        return Agent(**agent_args, model=openrouter_model_provider.get_model(model_name, openrouter_client))

    # no matching agents
    else:
        raise ValueError(f"Unsupported model type: {model_type}.")


class OpenRouterModelProvider(ModelProvider):
    """Provider for OpenRouter models, allowing dynamic model in openai-agents."""
    def get_model(self, model_name: str, openrouter_client: AsyncOpenAI) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name, 
            openai_client=openrouter_client
        )


class BeatsAgent:
    def __init__(self, 
                 name: str, 
                 agent_host: str, 
                 agent_port: int, 
                 model_type: str,
                 model_name: str):
        self.name = name
        self.agent_host = agent_host
        self.agent_port = agent_port
        self.model_type = model_type
        self.model_name = model_name

        self.tool_list: List[Any] = []
        self.mcp_url_list: List[str] = []
        self.agent_card_json = None
        self.app = None
    
    def load_agent_card(self, card_path: str):
        """Load agent card from a TOML file."""
        with open(card_path, "rb") as f:
            self.agent_card_json = tomllib.load(f)

    def add_mcp_server(self, url: str):
        """Add a MCP server to the agent."""
        self.mcp_url_list.append(url)

    def run(self):
        """Run the agent."""

        # Ensure the agent card is loaded before running
        if not self.agent_card_json:
            raise ValueError("Agent card not loaded. Please load an agent card before running.")

        # Create the application instance
        self._make_app()

        # Start the server
        uvicorn.run(
            self.app,
            host=self.agent_host,
            port=self.agent_port,
        )

    def get_app(self) -> Optional[A2AStarletteApplication]:
        """Get the application instance for the agent."""
        return self.app
    
    def _make_app(self) -> None:
        """Asynchronously create the application instance for the agent."""
        self.app = A2AStarletteApplication(
            agent_card=AgentCard(**self.agent_card_json),
            http_handler=DefaultRequestHandler(
                agent_executor=AgentBeatsExecutor(
                    agent_card_json=self.agent_card_json,
                    model_type=self.model_type,
                    model_name=self.model_name,
                    mcp_url_list=self.mcp_url_list,
                    tool_list=self.tool_list,
                ),
                task_store=InMemoryTaskStore(),
            ),
        ).build()

    def tool(self, name: str = None):
        """Decorator to register a function as a tool for the agent."""
        def decorator(func):
            # Use function name if no name provided
            tool_name = name or func.__name__
            
            # Apply the @function_tool decorator from agents library
            # This creates the proper tool format for openai-agents
            tool_func = function_tool(name_override=tool_name)(func)
            
            # Add to the tool list
            self.tool_list.append(tool_func)
            
            return func
        return decorator

    def register_tool(self, func: Callable, *, name: str | None = None):
        tool_name = name or func.__name__
        wrapped_tool = function_tool(name_override=tool_name)(func)
        self.tool_list.append(wrapped_tool)
        return wrapped_tool


class AgentBeatsExecutor(AgentExecutor):
    def __init__(self, agent_card_json: Dict[str, Any], 
                        model_type: str,
                        model_name: str,
                        mcp_url_list: Optional[List[str]] = None, 
                        tool_list: Optional[List[Any]] = None):
        """ (Shouldn't be called directly) 
            Initialize the AgentBeatsExecutor with the MCP URL and agent card JSON. """
        self.agent_card_json = agent_card_json
        self.model_type = model_type
        self.model_name = model_name
        self.chat_history: List[Dict[str, str]] = []

        self.mcp_url_list = mcp_url_list or []
        self.mcp_list = [MCPServerSse(params={"url": url}) 
                         for url in self.mcp_url_list]
        self.tool_list = tool_list or []
        
        # construct self.AGENT_PROMPT with agent_card_json
        self.AGENT_PROMPT = str(agent_card_json["description"])
        self.AGENT_PROMPT += "\n\n"
        if "skills" in agent_card_json:
            self.AGENT_PROMPT += str(agent_card_json["skills"])

        self.main_agent = None

    async def _init_agent_and_mcp(self):
        """Initialize the main agent with the provided tools and MCP servers."""
        for mcp_server in self.mcp_list:
            await mcp_server.connect()
        
        self.main_agent = create_agent(
            agent_name=self.agent_card_json["name"],
            model_type=self.model_type,
            model_name=self.model_name,
            instructions=self.AGENT_PROMPT,
            tools=self.tool_list,
            mcp_servers=self.mcp_list,
        )

        # Print agent instructions for debugging
        print(f"[AgentBeatsExecutor] Initializing agent: {self.main_agent.name} with {len(self.tool_list)} tools and {len(self.mcp_list)} MCP servers.")
        print(f"[AgentBeatsExecutor] Agent instructions: {self.AGENT_PROMPT}")
        

    async def invoke_agent(self, context: RequestContext) -> str:
        """Run a single turn of conversation through *self.main_agent*."""
        # Init agent and MCP servers if not already done
        # Must initialize here, because agent init and server run (mcp serve) must be in the same asyncio loop
        if not self.main_agent:
            await self._init_agent_and_mcp()
        
        # print agent input
        print(f"[AgentBeatsExecutor] Agent input: {context.get_user_input()}")

        # Build contextual chat input for the runner
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(),
            "role": "user",
        }]

        result = await Runner.run(self.main_agent, query_ctx, max_turns=30)
        self.chat_history = result.to_input_list()

        # print agent output
        print(f"[AgentBeatsExecutor] Agent output: {result.final_output}")

        return result.final_output

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # make / get current task
        task = context.current_task
        if task is None: # first chat
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        # push "working now" status
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("working...", task.contextId, task.id),
        )

        # await llm response
        reply_text = await self.invoke_agent(context)

        # push final response
        await updater.add_artifact(
            [Part(root=TextPart(text=reply_text))],
            name="response",
        )
        await updater.complete()

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not implemented yet)."""
        raise NotImplementedError("cancel not supported")

    async def cleanup(self) -> None:
        """Clean up MCP connections."""
        if self.mcp_list:
            for mcp_server in self.mcp_list:
                try:
                    await mcp_server.close()
                except Exception as e:
                    print(f"Warning: Error closing MCP server: {e}")
