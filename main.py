# C:\Users\drlor\OneDrive\Desktop\mycompany\main.py

import asyncio
from agents.chat_space_env import ChatSpace
from agents.base_agent import BaseAgent
from threading import Thread

# Initialize the chat space
chat_space = ChatSpace()

def start_agent(name, role, channel):
    agent = BaseAgent(chat_space=chat_space, name=name, role=role, channel=channel)
    asyncio.run(agent.run('smollm2:1.7b'))

if __name__ == "__main__":
    # Define company structure
    agents = [
        ("HR_Agent", "HR", "Tech"),
        ("Manager_Agent", "Management", "Tech"),
        ("python_agent", "General", "Tech"),
        ("Operations_Agent", "General", "Tech"),
    ]

    # Start agents in separate threads
    agent_threads = []
    for name, role, channel in agents:
        agent_thread = Thread(target=start_agent, args=(name, role, channel))
        agent_thread.daemon = True
        agent_threads.append(agent_thread)
        agent_thread.start()

    # Run the chat GUI in the main thread
    chat_space.run_gui()
