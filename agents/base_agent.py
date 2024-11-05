# C:\Users\drlor\OneDrive\Desktop\mycompany\agents\base_agent.py

import json
import logging
import asyncio
import ollama
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from .chat_space_env import ChatSpace

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_logs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base agent class with enhanced functionality for handling chat operations and tool usage.
    """
    
    TOOLSETS = {
        'HR': [
            'list_employees', 'add_employee', 'remove_employee', 
            'generate_report', 'log_activity', 'update_employee'
        ],
        'Management': [
            'list_employees', 'generate_report', 'log_activity',
            'broadcast_message', 'view_department_stats'
        ],
        'General': [
            'list_employees', 'log_activity', 'send_message',
            'change_channel', 'view_channel_history'
        ]
    }

    def __init__(
        self, 
        name: str, 
        role: str, 
        chat_space: ChatSpace, 
        channel: str = "General",
        message_cooldown: float = 2.0
    ):
        """
        Initialize the base agent with enhanced parameters and error checking.
        
        Args:
            name: Agent's name
            role: Agent's role (HR, Management, or General)
            chat_space: ChatSpace instance for communication
            channel: Initial channel to join
            message_cooldown: Minimum time between messages
        """
        if role not in self.TOOLSETS:
            raise ValueError(f"Invalid role: {role}. Must be one of {list(self.TOOLSETS.keys())}")
        
        self.name = name
        self.role = role
        self.chat_space = chat_space
        self.channel = channel
        self.message_cooldown = message_cooldown
        self.messages: List[Dict[str, Any]] = []
        self.activity_log: List[Dict[str, Any]] = []
        self.tools = self._get_tools_for_role(role)
        self.last_message = {
            'content': None,
            'timestamp': None
        }
        
        # Initialize employee data file path
        self.employee_file_path = Path(__file__).parent / 'employee_data' / 'employees.json'
        self._ensure_employee_file_exists()

    def _ensure_employee_file_exists(self) -> None:
        """Ensure the employee data file exists with proper structure."""
        if not self.employee_file_path.exists():
            self.employee_file_path.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "HR": [],
                "Management": [],
                "Tech": [],
                "General": []
            }
            with open(self.employee_file_path, 'w') as f:
                json.dump(initial_data, f, indent=2)

    def _get_tools_for_role(self, role: str) -> Dict[str, callable]:
        """Get available tools for the agent's role with error handling."""
        try:
            toolset = self.TOOLSETS.get(role, [])
            return {
                tool_name: getattr(self, tool_name)
                for tool_name in toolset
                if hasattr(self, tool_name)
            }
        except Exception as e:
            logger.error(f"Error getting tools for role {role}: {str(e)}")
            return {}

    async def _read_employee_data(self) -> Dict[str, List[Dict[str, str]]]:
        """Read employee data with error handling."""
        try:
            async with asyncio.Lock():
                with open(self.employee_file_path, 'r') as file:
                    return json.load(file)
        except Exception as e:
            logger.error(f"Error reading employee data: {str(e)}")
            return {}

    async def _write_employee_data(self, data: Dict[str, List[Dict[str, str]]]) -> bool:
        """Write employee data with error handling."""
        try:
            async with asyncio.Lock():
                with open(self.employee_file_path, 'w') as file:
                    json.dump(data, file, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing employee data: {str(e)}")
            return False

    async def list_employees(self, department: Optional[str] = None) -> str:
        """List employees with optional department filter."""
        if 'list_employees' not in self.tools:
            return "Access Denied: You do not have permission to list employees."
        
        employees = await self._read_employee_data()
        if department:
            return json.dumps({department: employees.get(department, [])}, indent=2)
        return json.dumps(employees, indent=2)

    async def add_employee(self, name: str, department: str, position: str) -> str:
        """Add an employee with enhanced validation."""
        if 'add_employee' not in self.tools:
            return "Access Denied: You do not have permission to add employees."
        
        if not all([name, department, position]):
            return "Error: All fields (name, department, position) are required."
        
        employees = await self._read_employee_data()
        if department not in employees:
            return f"Error: Invalid department '{department}'"
        
        # Check for duplicate employees
        if any(emp["name"] == name for emp in employees[department]):
            return f"Error: Employee '{name}' already exists in {department}"
        
        employees[department].append({
            "name": name,
            "position": position,
            "hire_date": datetime.now().isoformat()
        })
        
        if await self._write_employee_data(employees):
            await self.log_activity(f"Added employee {name} to {department} as {position}")
            return f"Successfully added employee {name} to {department} as {position}."
        return "Error: Failed to add employee"

    async def update_employee(self, name: str, department: str, new_position: Optional[str] = None) -> str:
        """Update employee information."""
        if 'update_employee' not in self.tools:
            return "Access Denied: You do not have permission to update employees."
        
        employees = await self._read_employee_data()
        if department not in employees:
            return f"Error: Department '{department}' not found"
        
        for emp in employees[department]:
            if emp["name"] == name:
                if new_position:
                    emp["position"] = new_position
                if await self._write_employee_data(employees):
                    await self.log_activity(f"Updated employee {name} in {department}")
                    return f"Successfully updated employee {name}."
                return "Error: Failed to update employee"
        
        return f"Error: Employee '{name}' not found in {department}"

    async def view_department_stats(self, department: Optional[str] = None) -> str:
        """Generate department statistics."""
        if 'view_department_stats' not in self.tools:
            return "Access Denied: You do not have permission to view department stats."
        
        employees = await self._read_employee_data()
        stats = {}
        
        for dept, emps in employees.items():
            if department and dept != department:
                continue
            stats[dept] = {
                "total_employees": len(emps),
                "positions": {}
            }
            for emp in emps:
                pos = emp["position"]
                stats[dept]["positions"][pos] = stats[dept]["positions"].get(pos, 0) + 1
        
        return json.dumps(stats, indent=2)

    async def view_channel_history(self, limit: int = 10) -> str:
        """View recent channel history."""
        if 'view_channel_history' not in self.tools:
            return "Access Denied: You do not have permission to view channel history."
        
        messages = self.chat_space.channels[self.channel][-limit:]
        return json.dumps({
            "channel": self.channel,
            "messages": messages
        }, indent=2)

    async def send_message(self, target_channel: str, content: str) -> None:
        """Send a message with rate limiting and duplicate prevention."""
        if 'send_message' not in self.tools:
            return "Access Denied: You do not have permission to send messages."
        
        current_time = datetime.now()
        
        # Check message cooldown
        if (self.last_message['timestamp'] and 
            (current_time - self.last_message['timestamp']).total_seconds() < self.message_cooldown):
            return
        
        # Avoid duplicate messages
        if content != self.last_message['content']:
            self.chat_space.display_message(self.name, content, target_channel)
            self.chat_space.send_message(target_channel, self.name, content)
            self.last_message = {
                'content': content,
                'timestamp': current_time
            }

    async def run(self, model: str) -> None:
        """Run the agent with enhanced error handling and monitoring."""
        client = ollama.AsyncClient()
        await self.send_message(self.channel, f"{self.name} is online.")
        logger.info(f"Agent {self.name} started in channel {self.channel}")

        async def message_handler():
            await self.chat_space.listen_to_channel(self.channel, self.receive_message)

        try:
            message_task = asyncio.create_task(message_handler())
            
            while True:
                try:
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
                                function_response = await self.tools[func_name](**args)
                            else:
                                function_response = "Unauthorized tool usage."
                            
                            self.messages.append({
                                'role': 'tool',
                                'content': function_response
                            })

                    final_response = await client.chat(model=model, messages=self.messages)
                    await self.send_message(self.channel, final_response['message']['content'])
                    
                except Exception as e:
                    logger.error(f"Error in agent {self.name} main loop: {str(e)}")
                    await asyncio.sleep(5)  # Back off on error
                    continue
                
                await asyncio.sleep(self.message_cooldown)
                
        except Exception as e:
            logger.error(f"Critical error in agent {self.name}: {str(e)}")
            await self.send_message(self.channel, f"{self.name} is going offline due to an error.")
        finally:
            message_task.cancel()
            logger.info(f"Agent {self.name} shutting down")