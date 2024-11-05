# C:\Users\drlor\OneDrive\Desktop\mycompany\agents\testagent.py

from .base_agent import BaseAgent

class TestAgent(BaseAgent):
    def __init__(self, chat_space, name="TestAgent", role="General", channel="General"):
        super().__init__(name=name, role=role, chat_space=chat_space, channel=channel)
