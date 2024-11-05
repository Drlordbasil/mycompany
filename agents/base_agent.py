# C:\Users\drlor\OneDrive\Desktop\mycompany\agents\base_agent.py

import json
import ollama
import asyncio
from pathlib import Path
from .chat_space_env import ChatSpace

employee_file_path = Path(__file__).parent / 'employee_data' / 'employees.json'

class BaseAgent:
    TOOLSETS = {
        'HR': ['list_employees', 'add_employee', 'remove_employee', 'generate_report', 'log_activity'],
        'Management': ['list_employees', 'generate_report', 'log_activity', 'broadcast_message'],
        'General': ['list_employees', 'log_activity', 'send_message', 'change_channel']
    }

    def __init__(self, name, role, chat_space, channel="General"):
        self.name = name
        self.role = role
        self.chat_space = chat_space
        self.channel = channel
        self.messages = []
        self.activity_log = []
        self.tools = self._get_tools_for_role(role)

    def _get_tools_for_role(self, role):
        toolset = self.TOOLSETS.get(role, [])
        available_tools = {}
        for tool_name in toolset:
            available_tools[tool_name] = getattr(self, tool_name)
        return available_tools

    def list_employees(self) -> str:
        try:
            with open(employee_file_path, 'r') as file:
                employees = json.load(file)
            return json.dumps(employees, indent=2)
        except FileNotFoundError:
            return json.dumps({'error': 'Employee list not found'})
        except json.JSONDecodeError:
            return json.dumps({'error': 'Error reading employee data'})

    def add_employee(self, name, department, position) -> str:
        if 'add_employee' not in self.tools:
            return "Access Denied: You do not have permission to add employees."
        try:
            with open(employee_file_path, 'r+') as file:
                employees = json.load(file)
                if department not in employees:
                    employees[department] = []
                employees[department].append({"name": name, "position": position})
                file.seek(0)
                json.dump(employees, file, indent=2)
            return f"Employee {name} added to {department} as {position}."
        except Exception as e:
            return f"Failed to add employee: {str(e)}"

    def remove_employee(self, name, department) -> str:
        if 'remove_employee' not in self.tools:
            return "Access Denied: You do not have permission to remove employees."
        try:
            with open(employee_file_path, 'r+') as file:
                employees = json.load(file)
                if department in employees:
                    employees[department] = [emp for emp in employees[department] if emp["name"] != name]
                    file.seek(0)
                    json.dump(employees, file, indent=2)
                    file.truncate()
            return f"Employee {name} removed from {department}."
        except Exception as e:
            return f"Failed to remove employee: {str(e)}"

    def generate_report(self, department=None) -> str:
        if 'generate_report' not in self.tools:
            return "Access Denied: You do not have permission to generate reports."
        try:
            with open(employee_file_path, 'r') as file:
                employees = json.load(file)
            if department:
                return json.dumps({department: employees.get(department, [])}, indent=2)
            return json.dumps(employees, indent=2)
        except FileNotFoundError:
            return json.dumps({'error': 'Employee data not found'})
        except json.JSONDecodeError:
            return json.dumps({'error': 'Error reading employee data'})

    def log_activity(self, activity):
        if 'log_activity' not in self.tools:
            return "Access Denied: You do not have permission to log activity."
        self.activity_log.append(activity)
        self.chat_space.display_message(self.name, f"Logged activity: {activity}", self.channel)

    def broadcast_message(self, content):
        if 'broadcast_message' not in self.tools:
            return "Access Denied: You do not have permission to broadcast messages."
        for channel in self.chat_space.channels.keys():
            self.chat_space.send_message(channel, self.name, f"[Broadcast] {content}")

    async def send_message(self, target_channel, content):
        if 'send_message' not in self.tools:
            return "Access Denied: You do not have permission to send messages."
        self.chat_space.display_message(self.name, content, target_channel)
        self.chat_space.send_message(target_channel, self.name, content)

    def change_channel(self, new_channel):
        if 'change_channel' not in self.tools:
            return "Access Denied: You do not have permission to change channels."
        if new_channel in self.chat_space.channels:
            self.chat_space.display_message(self.name, f"Switched to {new_channel}", self.channel)
            self.channel = new_channel
            return f"{self.name} switched to {new_channel}."
        else:
            return f"Channel '{new_channel}' does not exist."

    async def receive_message(self, message):
        content = message['content']
        self.chat_space.display_message(message['sender'], content, self.channel)
        self.messages.append({'role': 'user', 'content': content})

    async def run(self, model: str):
        client = ollama.AsyncClient()
        await self.send_message(self.channel, f"{self.name} is online.")

        asyncio.create_task(self.chat_space.listen_to_channel(self.channel, self.receive_message))

        while True:
            response = await client.chat(
                model=model,
                messages=self.messages,
                tools=[{
                    'type': 'function',
                    'function': {
                        'name': tool_name,
                        'description': f"Tool: {tool_name}",
                        'parameters': {'type': 'object', 'properties': {}},
                    },
                } for tool_name in self.tools],
            )
            self.messages.append(response['message'])

            if response['message'].get('tool_calls'):
                for tool in response['message']['tool_calls']:
                    func_name = tool['function']['name']
                    args = tool['function']['arguments']
                    if func_name in self.tools:
                        function_response = self.tools[func_name](**args)
                    else:
                        function_response = "Unauthorized tool usage."
                    self.messages.append({'role': 'tool', 'content': function_response})

            final_response = await client.chat(model=model, messages=self.messages)
            self.chat_space.display_message(self.name, final_response['message']['content'], self.channel)
            await asyncio.sleep(2)
