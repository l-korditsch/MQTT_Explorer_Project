import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import paho.mqtt.client as mqtt
from datetime import datetime
import sqlite3
import threading
import ssl

class MQTTExplorer:
    def __init__(self, root):
        # Ensure storage folder exists
        os.makedirs("./Storage/", exist_ok=True)

        self.root = root
        self.root.title("MQTT Explorer")
        
        # Configure main window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # Initialize database
        self.init_database()
        
        # Initialize threading lock for database
        self.db_lock = threading.Lock()
        
        # Connection Frame
        self.conn_frame = ttk.LabelFrame(root, text="Connection Settings", padding="5")
        self.conn_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Broker settings
        ttk.Label(self.conn_frame, text="Broker:").grid(row=0, column=0, padx=5, pady=5)
        self.broker = ttk.Combobox(self.conn_frame, width=30)
        self.broker['values'] = self.loadBrokersFromFile()
        self.broker.set("localhost")

        self.broker.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.conn_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5)
        self.port = ttk.Combobox(self.conn_frame, width=30)
        self.port['values'] = self.loadPortsFromFile()
        self.port.set("1883")
        self.port.grid(row=1, column=1, padx=5, pady=5)
        
        # Status indicator
        self.status_label = ttk.Label(self.conn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Connect button
        self.connect_btn = ttk.Button(self.conn_frame, text="Connect", command=self.connect)
        self.connect_btn.grid(row=3, column=0, columnspan=2, pady=5)

        #Disconnect button
        self.disconnect_btn = ttk.Button(self.conn_frame, text="Disconnect", command=self.disconnect)
        self.disconnect_btn.grid(row=4, column=0, columnspan=2, pady=5)

        # Subscribe Frame
        self.sub_frame = ttk.LabelFrame(root, text="Subscribe", padding="5")
        self.sub_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(self.sub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        
        # Combobox with existing topics
        self.topic = ttk.Combobox(self.sub_frame, width=30)
        self.topic['values'] = self.loadTopicsFromFile()
        self.topic.set("#")

        self.topic.grid(row=0, column=1, padx=5, pady=5)
        
        # Subscribe button
        self.subscribe_btn = ttk.Button(self.sub_frame, text="Subscribe", command=self.subscribe)
        self.subscribe_btn.grid(row=1, column=0, columnspan=2, pady=5)

        # Unsubscribe button
        self.unsubscribe_btn = ttk.Button(self.sub_frame, text="Unsubscribe", command=self.unsubscribe)
        self.unsubscribe_btn.grid(row=1, column=2, columnspan=2, pady=5)

        # Publish Frame
        self.pub_frame = ttk.LabelFrame(root, text="Publish", padding="5")
        self.pub_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(self.pub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        self.pub_topic = ttk.Combobox(self.pub_frame, width=30)
        self.pub_topic['values'] = self.loadTopicsFromFile()
        self.pub_topic.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.pub_frame, text="Message:").grid(row=1, column=0, padx=5, pady=5)
        self.pub_message = ttk.Entry(self.pub_frame, width=30)
        self.pub_message.grid(row=1, column=1, padx=5, pady=5)
        
        self.publish_btn = ttk.Button(self.pub_frame, text="Publish", command=self.publish)
        self.publish_btn.grid(row=2, column=0, columnspan=2, pady=5)

        # Messages Frame with Scrolled Text
        self.msg_frame = ttk.LabelFrame(root, text="Messages", padding="5")
        self.msg_frame.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
        
        # Button frame for message controls
        self.msg_btn_frame = ttk.Frame(self.msg_frame)
        self.msg_btn_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.clear_msg_btn = ttk.Button(self.msg_btn_frame, text="Clear Messages", command=self.clearMessages)
        self.clear_msg_btn.grid(row=0, column=0, padx=5, pady=5)
        self.clear_db_btn = ttk.Button(self.msg_btn_frame, text="Clear Database", command=self.clear_database)
        self.clear_db_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.show_db_btn = ttk.Button(self.msg_btn_frame, text="Show Database", command=self.show_database_window)
        self.show_db_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.show_db_ui_btn = ttk.Button(self.msg_btn_frame, text="Show DB in UI", command=self.show_database_in_ui)
        self.show_db_ui_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.messages = scrolledtext.ScrolledText(self.msg_frame, height=10, width=100)
        self.messages.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('mqtt_messages.db', check_same_thread=False)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                    (timestamp TEXT, topic TEXT, message TEXT)''')
        self.conn.commit()

    def save_message(self, timestamp, topic, message):
        """Save message to database"""
        with self.db_lock:
            c = self.conn.cursor()
            c.execute("INSERT INTO messages VALUES (?,?,?)", (timestamp, topic, message))
            self.conn.commit()

    def connect(self):
        try:
            broker = self.broker.get()
            port = int(self.port.get())
            # Store port
            self.storePortToFile(str(port)) 
            self.refreshPortCombobox()

            # Store broker in file
            self.storeBrokerToFile(broker)
            
            # Disconnect existing client if any
            if hasattr(self, 'client'):
                self.client.loop_stop()
                self.client.disconnect()
            
            # Create new client instance with clean session
            client_id = f'python-mqtt-{datetime.now().strftime("%H%M%S")}'
            self.client = mqtt.Client(client_id=client_id, clean_session=True)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # Try SSL for secure connection if using port 8883
            if port == 8883:
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)  # Don't verify certificate
                self.client.tls_insecure_set(True)  # Don't verify hostname
                
            # Increase timeouts for more stability
            self.client._connect_timeout = 30
            self.client._keepalive = 60
            
            # Update status before connecting
            self.status_label.config(text="Status: Connecting...", foreground="orange")
            self.log_message(f"Connecting to {broker}:{port}...")
            
            # Try to connect
            self.client.connect(broker, port)
            self.client.loop_start()
                
        except Exception as e:
            self.log_message(f"Connection failed: {str(e)}")
            self.status_label.config(text="Status: Error", foreground="red")

    def disconnect(self):
        """Disconnect from the broker"""
        if self.client.is_connected():
            self.client.disconnect()
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.log_message("Disconnected from broker")
        else:
            self.log_message("Error: Not connected to broker")
    
    def subscribe(self):
        topic = self.topic.get()
        # Store used topic to file
        self.storeTopicToFile(topic)

        if not self.client.is_connected():
            self.log_message("Error: Not connected to broker")
            return

        #TODO self.client.unsubscribe(topic)  # Ensure we are not subscribed before subscribing
        topic = self.topic.get()
        self.client.subscribe(topic)
        self.log_message(f"Subscribed to {topic}")

    def unsubscribe(self):
        if not self.client.is_connected():
            self.log_message("Error: Not connected to broker")
            return
        topic = self.topic.get()
        if topic == "#":
            self.disconnect()
            self.log_message(f"Error: Cannot unsubscribe from {topic} topics")
            return
        self.client.unsubscribe(topic)
        self.log_message(f"Unsubscribed from {topic}")

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

    def on_connect(self, _client, _userdata, _flags, rc):
        if rc == 0:
            self.log_message("Connected successfully")
            self.status_label.config(text="Status: Connected", foreground="green")
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error = error_messages.get(rc, f"Connection failed with code {rc}")
            self.log_message(error)
            self.status_label.config(text=f"Status: Error ({rc})", foreground="red")

    def on_disconnect(self, _client, _userdata, rc):
        disconnect_reasons = {
            0: "Clean disconnect",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized",
            6: "Connection lost",
            7: "Connection timed out or network error"
        }
        reason = disconnect_reasons.get(rc, f"Unknown error (code={rc})")
        self.log_message(f"Disconnected: {reason}")
        self.status_label.config(text="Status: Disconnected", foreground="red")

    def on_message(self, _client, _userdata, msg):
        """Handle received messages"""
        current_time = datetime.now().strftime("%H%M%S")
        try:
            # Attempt to decode the payload as UTF-8
            message = msg.payload.decode('utf-8')
        except UnicodeDecodeError:
            # Handle non-UTF-8 payloads
            message = f"<Binary Data: {msg.payload.hex()}>"

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
    
    def storeTopicToFile(self, topic, filename="topics.txt"):
        if not topic:
            self.log_message("No topic to store.")
            return
        try:
            # Load existing topics from JSON file, or start a new list
            if os.path.exists("./Storage/" + filename):
                with open("./Storage/" + filename, "r") as file:
                    try:
                        topics = json.load(file)
                    except json.JSONDecodeError:
                        topics = []
            else:
                topics = []

            # Add the topic if not already present
            if topic not in topics:
                topics.append(topic)
                with open("./Storage/" + filename, "w") as file:
                    json.dump(topics, file, indent=2)
                self.log_message(f"Saved new topic '{topic}' to {filename}")
                self.refreshTopicCombobox()
            else:
                self.log_message(f"Topic '{topic}' already saved")

        except Exception as e:
            self.log_message(f"Failed to save topic: {e}")

    def loadTopicsFromFile(self, filename="topics.txt"):
        if not os.path.exists("./Storage/" + filename):
            return []

        try:
            with open("./Storage/" + filename, "r") as file:
                topics = json.load(file)
                if isinstance(topics, list):
                    return topics
                else:
                    self.log_message("Invalid format in topics file.")
                    return []
        except (json.JSONDecodeError, Exception) as e:
            self.log_message(f"Failed to load topics: {e}")
            return []
        
    def refreshTopicCombobox(self):
        topics = self.loadTopicsFromFile()
        self.topic['values'] = topics

    def storeBrokerToFile(self, broker, filename="brokers.txt"):
        if not broker:
            self.log_message("No broker to store.")
            return
        try:
            # Load existing brokers from file
            if os.path.exists("./Storage/" + filename):
                with open("./Storage/" + filename, "r") as file:
                    try:
                        brokers = json.load(file)
                    except json.JSONDecodeError:
                        brokers = []
            else:
                brokers = []

            # Save new broker if not already in list
            if broker not in brokers:
                brokers.append(broker)
                with open("./Storage/" + filename, "w") as file:
                    json.dump(brokers, file, indent=2)
                self.log_message(f"Saved new broker '{broker}' to {filename}")
                self.refreshBrokerCombobox()
            else:
                self.log_message(f"Broker '{broker}' already saved")

        except Exception as e:
            self.log_message(f"Failed to save broker: {e}")

    def loadBrokersFromFile(self, filename="brokers.txt"):
        if not os.path.exists("./Storage/" + filename):
            return []
        try:
            with open("./Storage/" + filename, "r") as file:
                brokers = json.load(file)
                return brokers if isinstance(brokers, list) else []
        except Exception:
            return []
        
    def refreshBrokerCombobox(self):
        brokers = self.loadBrokersFromFile()
        self.broker['values'] = brokers

    def storePortToFile(self, port, filename="ports.txt"):
        if not port:
            self.log_message("No port to store.")
            return
        try:
            if os.path.exists("./Storage/" + filename):
                with open("./Storage/" + filename, "r") as file:
                    try:
                        ports = json.load(file)
                    except json.JSONDecodeError:
                        ports = []
            else:
                ports = []

            if port not in ports:
                ports.append(port)
                with open("./Storage/" + filename, "w") as file:
                    json.dump(ports, file, indent=2)
                self.log_message(f"Saved new port '{port}' to {filename}")
            else:
                self.log_message(f"Port '{port}' already saved")
        except Exception as e:
            self.log_message(f"Failed to save port: {e}")
    
    def loadPortsFromFile(self, filename="ports.txt"):
        if not os.path.exists("./Storage/" + filename):
            return []
        try:
            with open("./Storage/" + filename, "r") as file:
                ports = json.load(file)
                return ports if isinstance(ports, list) else []
        except Exception:
            return []
        
    def refreshPortCombobox(self):
        ports = self.loadPortsFromFile()
        self.port['values'] = ports

    def clearMessages(self):
        self.messages.delete('1.0', tk.END)

    def clear_database(self):
        """Clear the messages database"""
        with self.db_lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM messages")
            self.conn.commit()
            self.log_message("Database cleared")

    def show_database_window(self):
        """Show the database contents in a new window"""
        db_window = tk.Toplevel(self.root)
        db_window.title("Database Contents")
        db_window.geometry("800x600")
        
        # Configure grid weights for resizing
        db_window.columnconfigure(0, weight=1)
        db_window.rowconfigure(0, weight=1)
        
        # Create frame for controls
        control_frame = ttk.Frame(db_window)
        control_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Add refresh button
        refresh_btn = ttk.Button(control_frame, text="Refresh", command=lambda: self.refresh_database_view(tree, count_label))
        refresh_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Add export button
        export_btn = ttk.Button(control_frame, text="Export to File", command=lambda: self.export_database())
        export_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Add count label
        count_label = ttk.Label(control_frame, text="")
        count_label.grid(row=0, column=2, padx=20, pady=5)
        
        tree = ttk.Treeview(db_window, columns=("Timestamp", "Topic", "Message"), show='headings')
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Topic", text="Topic")
        tree.heading("Message", text="Message")
        
        # Configure column widths
        tree.column("Timestamp", width=100)
        tree.column("Topic", width=200)
        tree.column("Message", width=400)
        
        tree.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(db_window, orient="vertical", command=tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        tree.configure(yscroll=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(db_window, orient="horizontal", command=tree.xview)
        h_scrollbar.grid(row=2, column=0, sticky='ew')
        tree.configure(xscroll=h_scrollbar.set)

        # Load initial data
        self.refresh_database_view(tree, count_label)

    def refresh_database_view(self, tree, count_label=None):
        """Refresh the database view with current data"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Insert data into the treeview
        with self.db_lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM messages ORDER BY timestamp DESC")
            rows = c.fetchall()
            for row in rows:
                tree.insert("", "end", values=row)
                
        # Update count if label provided
        if count_label:
            count_label.config(text=f"Total messages: {len(rows)}")

    def export_database(self):
        """Export database contents to a JSON file"""
        try:
            with self.db_lock:
                c = self.conn.cursor()
                c.execute("SELECT * FROM messages")
                rows = c.fetchall()
                
            # Create export data
            export_data = []
            for row in rows:
                export_data.append({
                    "timestamp": row[0],
                    "topic": row[1],
                    "message": row[2]
                })
            
            # Save to file
            filename = f"mqtt_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join("./Storage/", filename)
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            self.log_message(f"Database exported to {filename}")
            
        except Exception as e:
            self.log_message(f"Failed to export database: {e}")

    def show_database_in_ui(self):
        """Show recent database entries in the main UI"""
        try:
            with self.db_lock:
                c = self.conn.cursor()
                c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 10")
                rows = c.fetchall()
                
            self.log_message("--- Recent Database Entries ---")
            for row in rows:
                timestamp, topic, message = row
                self.log_message(f"[{timestamp}] {topic}: {message}")
            self.log_message("--- End Database Entries ---")
            
        except Exception as e:
            self.log_message(f"Failed to show database: {e}")

#TODO Add auto scaling of HUD to window size
#TODO Add a button to disable autoscroll
#TODO Add a button to enable autoscroll maybe same button as above
#TODO Prettefy the whole interface
#TODO Add a function to clear the database
#TODO Add a function to show the database
#TODO Add a function to show the database in the UI
#TODO Add a function to show the database in a new window
#TODO Add a function to show the database in a new window with a table

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTExplorer(root)
    root.mainloop()