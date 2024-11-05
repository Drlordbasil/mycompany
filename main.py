# C:\Users\drlor\OneDrive\Desktop\mycompany\main.py

import asyncio
from agents.chat_space_env import ChatSpace
from agents.testagent import TestAgent
from threading import Thread

# Initialize the chat space
chat_space = ChatSpace()

def start_agent(name, channel):
    test_agent = TestAgent(chat_space=chat_space, name=name, role="General", channel=channel)
    asyncio.run(test_agent.run('mistral'))

if __name__ == "__main__":
    # Start test agents in separate threads
    agent_thread_1 = Thread(target=start_agent, args=("TestAgent1", "General"))
    agent_thread_2 = Thread(target=start_agent, args=("TestAgent2", "Tech"))
    
    agent_thread_1.daemon = True
    agent_thread_2.daemon = True
    
    agent_thread_1.start()
    agent_thread_2.start()

    # Run the chat GUI in the main thread
    chat_space.run_gui()
