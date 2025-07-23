#!/bin/bash

unset TMUX
SESSION="agents_session"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null

# Pane 4: Launch Blue Agent
CMD1="source venv/bin/activate && agentbeats run blue_agent/blue_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --agent_port 9011 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool blue_agent/tools.py; exec $SHELL"
# Pane 5: Launch Red Agent
CMD2="source venv/bin/activate && agentbeats run red_agent/red_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9020 --agent_port 9021 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool red_agent/tools.py; exec $SHELL"
# Pane 6: Launch Green Agent
CMD3="source venv/bin/activate && agentbeats run green_agent/green_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9030 --agent_port 9031 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool green_agent/tools.py; exec $SHELL"

# Start a new tmux session in detached mode with the first pane
tmux new-session -d -s $SESSION "$CMD1"

# Split and run the other commands
tmux split-window -t $SESSION:0 "$CMD2"
tmux select-layout -t $SESSION:0 tiled
tmux split-window -t $SESSION:0 "$CMD3"
tmux select-layout -t $SESSION:0 tiled

# Attach to the session
tmux attach-session -t $SESSION
