# C:\Users\drlor\OneDrive\Desktop\mycompany\agents\chat_space_env.py

from collections import defaultdict
import asyncio
import tkinter as tk
from tkinter import ttk
from threading import Thread

class ChatSpace:
    def __init__(self):
        self.channels = defaultdict(list)
        self.root = tk.Tk()
        self.root.title("Agent Chat Space")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f2f5")

        # Style setup
        style = ttk.Style()
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))

        # Main Frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Channel selection
        self.channel_var = tk.StringVar(self.root)
        self.channel_var.set("General")
        channel_label = ttk.Label(main_frame, text="Channel:")
        channel_label.grid(row=0, column=0, sticky="w")
        
        self.channel_dropdown = ttk.Combobox(
            main_frame, textvariable=self.channel_var, values=["General", "HR", "Management", "Tech"], state="readonly", width=10
        )
        self.channel_dropdown.grid(row=0, column=1, sticky="w")

        # Message area
        self.message_area = tk.Text(main_frame, wrap='word', state='disabled', bg="#ffffff", fg="#333333", font=("Segoe UI", 10))
        self.message_area.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        main_frame.rowconfigure(1, weight=1)  # Allow text area to expand

        # Message entry
        self.entry_field = ttk.Entry(main_frame)
        self.entry_field.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="ew")
        self.entry_field.bind("<Return>", lambda event: self.send_user_message())

        # Send button
        self.send_button = ttk.Button(main_frame, text="Send", command=self.send_user_message, width=8)
        self.send_button.grid(row=2, column=2, padx=5, pady=10, sticky="e")

    def display_message(self, sender, content, channel):
        """Display a message in the chat area with proper formatting."""
        self.message_area.configure(state='normal')
        self.message_area.insert('end', f"[{channel}] {sender}: {content}\n", "message")
        self.message_area.see('end')
        self.message_area.configure(state='disabled')

    def send_message(self, channel, sender, content):
        """Send a message to a specified channel."""
        message = {'sender': sender, 'content': content}
        self.channels[channel].append(message)
        self.display_message(sender, content, channel)

    def get_messages(self, channel):
        """Retrieve all messages from a specific channel."""
        return self.channels[channel]

    def send_user_message(self):
        """Send the user's message to the current channel."""
        content = self.entry_field.get().strip()
        if content:
            current_channel = self.channel_var.get()
            self.send_message(current_channel, "@AnthonySnider", content)
            self.entry_field.delete(0, 'end')
        
    def run_gui(self):
        """Run the Tkinter mainloop."""
        self.root.mainloop()

    async def listen_to_channel(self, channel, callback, check_interval=2):
        """Continuously listen to a channel and trigger a callback for new messages."""
        processed_count = 0
        while True:
            messages = self.channels[channel]
            new_messages = messages[processed_count:]
            for message in new_messages:
                await callback(message)
            processed_count = len(messages)
            await asyncio.sleep(check_interval)

    def clear_channel(self, channel):
        """Clear all messages from a specific channel."""
        self.channels[channel].clear()

    def start(self):
        """Start the GUI in a separate thread."""
        gui_thread = Thread(target=self.run_gui)
        gui_thread.daemon = True
        gui_thread.start()
