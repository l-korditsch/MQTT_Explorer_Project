import tkinter as tk
from tkinter import ttk, scrolledtext
import paho.mqtt.client as mqtt
from datetime import datetime
import sqlite3
import json

class MQTTExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Explorer")
        
        # Configure main window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # Initialize database
        self.init_database()
        
        # Connection Frame
        self.conn_frame = ttk.LabelFrame(root, text="Connection Settings", padding="5")
        self.conn_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Broker settings
        ttk.Label(self.conn_frame, text="Broker:").grid(row=0, column=0, padx=5, pady=5)
        self.broker = ttk.Entry(self.conn_frame, width=30)
        self.broker.insert(0, "localhost")
        self.broker.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.conn_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5)
        self.port = ttk.Entry(self.conn_frame, width=30)
        self.port.insert(0, "1883")
        self.port.grid(row=1, column=1, padx=5, pady=5)
        
        # Status indicator
        self.status_label = ttk.Label(self.conn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Connect button
        self.connect_btn = ttk.Button(self.conn_frame, text="Connect", command=self.connect)
        self.connect_btn.grid(row=3, column=0, columnspan=2, pady=5)

        # Subscribe Frame
        self.sub_frame = ttk.LabelFrame(root, text="Subscribe", padding="5")
        self.sub_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(self.sub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        self.topic = ttk.Entry(self.sub_frame, width=30)
        self.topic.insert(0, "#")
        self.topic.grid(row=0, column=1, padx=5, pady=5)
        
        self.subscribe_btn = ttk.Button(self.sub_frame, text="Subscribe", command=self.subscribe)
        self.subscribe_btn.grid(row=1, column=0, columnspan=2, pady=5)

        # Publish Frame
        self.pub_frame = ttk.LabelFrame(root, text="Publish", padding="5")
        self.pub_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(self.pub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        self.pub_topic = ttk.Entry(self.pub_frame, width=30)
        self.pub_topic.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.pub_frame, text="Message:").grid(row=1, column=0, padx=5, pady=5)
        self.pub_message = ttk.Entry(self.pub_frame, width=30)
        self.pub_message.grid(row=1, column=1, padx=5, pady=5)
        
        self.publish_btn = ttk.Button(self.pub_frame, text="Publish", command=self.publish)
        self.publish_btn.grid(row=2, column=0, columnspan=2, pady=5)

        # Messages Frame with Scrolled Text
        self.msg_frame = ttk.LabelFrame(root, text="Messages", padding="5")
        self.msg_frame.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
        
        self.messages = scrolledtext.ScrolledText(self.msg_frame, height=10, width=50)
        self.messages.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('mqtt_messages.db')
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                    (timestamp TEXT, topic TEXT, message TEXT)''')
        self.conn.commit()

    def save_message(self, timestamp, topic, message):
        """Save message to database"""
        c = self.conn.cursor()
        c.execute("INSERT INTO messages VALUES (?,?,?)", (timestamp, topic, message))
        self.conn.commit()

    def connect(self):
        try:
            # Update default broker to test.mosquitto.org
            if self.broker.get() == "localhost":
                self.broker.delete(0, tk.END)
                self.broker.insert(0, "test.mosquitto.org")
            
            # Set clean session
            self.client = mqtt.Client(clean_session=True)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # Connect with keepalive of 60 seconds
            self.client.connect(self.broker.get(), int(self.port.get()), 60)
            self.client.loop_start()
            
            # Update status immediately
            self.status_label.config(text="Status: Connecting...", foreground="orange")
            self.log_message(f"Connecting to {self.broker.get()}:{self.port.get()}...")
            
        except Exception as e:
            self.log_message(f"Connection failed: {str(e)}")
            self.status_label.config(text="Status: Error", foreground="red")
    
    def subscribe(self):
        if not self.client.is_connected():
            self.log_message("Error: Not connected to broker")
            return
        topic = self.topic.get()
        self.client.subscribe(topic)
        self.log_message(f"Subscribed to {topic}")

    def publish(self):
        if not self.client.is_connected():
            self.log_message("Error: Not connected to broker")
            return
        topic = self.pub_topic.get()
        message = self.pub_message.get()
        self.client.publish(topic, message)
        self.log_message(f"Published to {topic}: {message}")
        
    def log_message(self, message):
        """Log message to UI"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.messages.insert('end', f"[{current_time}] {message}\n")
        self.messages.see('end')

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log_message("Connected successfully")
            self.status_label.config(text="Status: Connected", foreground="green")
        else:
            self.log_message(f"Connection failed with code {rc}")
            self.status_label.config(text="Status: Error", foreground="red")

    def on_disconnect(self, client, userdata, rc):
        self.log_message("Disconnected from broker")
        self.status_label.config(text="Status: Disconnected", foreground="red")

    def on_message(self, client, userdata, msg):
        """Handle received messages"""
        current_time = datetime.now().strftime("%H:%M:%S")
        message = msg.payload.decode()
        
        # Save to database
        self.save_message(current_time, msg.topic, message)
        
        # Display in UI
        self.log_message(f"{msg.topic}: {message}")

    def __del__(self):
        """Cleanup on exit"""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'client'):
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTExplorer(root)
    root.mainloop()