import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import paho.mqtt.client as mqtt
from datetime import datetime
import sqlite3
import threading
import ssl

class MQTTExplorer:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.setup_storage()
        self.setup_database()
        self.setup_mqtt()
        self.setup_bindings()
        
    def setup_ui(self):
        """Initialize the user interface"""
        self.root.title("MQTT Explorer Pro")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # Configure main window grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)
        
        # Autoscroll setting
        self.autoscroll_enabled = True
        
        # Create main interface
        self.create_connection_frame()
        self.create_subscribe_frame()
        self.create_publish_frame()
        self.create_controls_frame()
        self.create_messages_frame()
        
    def setup_storage(self):
        """Initialize storage directory"""
        os.makedirs("./Storage/", exist_ok=True)
        
    def setup_database(self):
        """Initialize SQLite database"""
        self.db_lock = threading.Lock()
        self.conn = sqlite3.connect('mqtt_messages.db', check_same_thread=False)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT, topic TEXT, message TEXT, qos INTEGER)''')
        self.conn.commit()
        
    def setup_mqtt(self):
        """Initialize MQTT client"""
        self.client = None
        self.is_connected = False
        
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind('<Control-Return>', lambda e: self.connect())
        self.pub_message.bind('<Return>', lambda e: self.publish())
        self.topic.bind('<Return>', lambda e: self.subscribe())
        
    def create_connection_frame(self):
        """Create connection settings frame"""
        frame = ttk.LabelFrame(self.root, text="🔗 Connection", padding="10")
        frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        frame.columnconfigure(1, weight=1)
        
        # Broker
        ttk.Label(frame, text="Broker:").grid(row=0, column=0, sticky="w", padx=(0,10))
        self.broker = ttk.Combobox(frame, width=25)
        self.broker['values'] = self.load_from_file("brokers.json") or ["localhost", "test.mosquitto.org"]
        self.broker.set("localhost")
        self.broker.grid(row=0, column=1, sticky="ew", padx=(0,10))
        
        # Port
        ttk.Label(frame, text="Port:").grid(row=0, column=2, sticky="w", padx=(10,5))
        self.port = ttk.Combobox(frame, width=10)
        self.port['values'] = self.load_from_file("ports.json") or ["1883", "8883", "8080"]
        self.port.set("1883")
        self.port.grid(row=0, column=3, sticky="w")
        
        # Auth frame
        auth_frame = ttk.Frame(frame)
        auth_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10,0))
        auth_frame.columnconfigure(1, weight=1)
        auth_frame.columnconfigure(3, weight=1)
        
        ttk.Label(auth_frame, text="Username:").grid(row=0, column=0, sticky="w", padx=(0,5))
        self.username = ttk.Entry(auth_frame, width=15)
        self.username.grid(row=0, column=1, sticky="ew", padx=(0,20))
        
        ttk.Label(auth_frame, text="Password:").grid(row=0, column=2, sticky="w", padx=(0,5))
        self.password = ttk.Entry(auth_frame, show="*", width=15)
        self.password.grid(row=0, column=3, sticky="ew")
        
        # Status and controls
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=2, column=0, columnspan=4, pady=(10,0))
        
        self.status_label = ttk.Label(status_frame, text="● Disconnected", foreground="red")
        self.status_label.pack(side="left")
        
        btn_frame = ttk.Frame(status_frame)
        btn_frame.pack(side="right")
        
        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self.connect)
        self.connect_btn.pack(side="left", padx=(0,5))
        
        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self.disconnect, state="disabled")
        self.disconnect_btn.pack(side="left")
        
    def create_subscribe_frame(self):
        """Create subscription frame"""
        frame = ttk.LabelFrame(self.root, text="📥 Subscribe", padding="10")
        frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        frame.columnconfigure(1, weight=1)
        
        ttk.Label(frame, text="Topic:").grid(row=0, column=0, sticky="w", padx=(0,10))
        self.topic = ttk.Combobox(frame)
        self.topic['values'] = self.load_from_file("topics.json") or ["#", "test/+", "home/+/temperature"]
        self.topic.set("#")
        self.topic.grid(row=0, column=1, sticky="ew", padx=(0,10))
        
        ttk.Label(frame, text="QoS:").grid(row=0, column=2, sticky="w", padx=(10,5))
        self.sub_qos = ttk.Combobox(frame, values=["0", "1", "2"], width=5, state="readonly")
        self.sub_qos.set("0")
        self.sub_qos.grid(row=0, column=3, padx=(0,10))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=4)
        
        self.subscribe_btn = ttk.Button(btn_frame, text="Subscribe", command=self.subscribe, state="disabled")
        self.subscribe_btn.pack(side="left", padx=(0,5))
        
        self.unsubscribe_btn = ttk.Button(btn_frame, text="Unsubscribe", command=self.unsubscribe, state="disabled")
        self.unsubscribe_btn.pack(side="left")
        
    def create_publish_frame(self):
        """Create publish frame"""
        frame = ttk.LabelFrame(self.root, text="📤 Publish", padding="10")
        frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        frame.columnconfigure(1, weight=1)
        
        # Topic row
        ttk.Label(frame, text="Topic:").grid(row=0, column=0, sticky="w", padx=(0,10))
        self.pub_topic = ttk.Combobox(frame)
        self.pub_topic['values'] = self.load_from_file("topics.json") or []
        self.pub_topic.grid(row=0, column=1, sticky="ew", padx=(0,10))
        
        ttk.Label(frame, text="QoS:").grid(row=0, column=2, sticky="w", padx=(10,5))
        self.pub_qos = ttk.Combobox(frame, values=["0", "1", "2"], width=5, state="readonly")
        self.pub_qos.set("0")
        self.pub_qos.grid(row=0, column=3, padx=(0,10))
        
        # Retain checkbox
        self.retain_var = tk.BooleanVar()
        self.retain_cb = ttk.Checkbutton(frame, text="Retain", variable=self.retain_var)
        self.retain_cb.grid(row=0, column=4)
        
        # Message row
        ttk.Label(frame, text="Message:").grid(row=1, column=0, sticky="w", padx=(0,10), pady=(10,0))
        self.pub_message = ttk.Entry(frame)
        self.pub_message.grid(row=1, column=1, sticky="ew", padx=(0,10), pady=(10,0))
        
        self.publish_btn = ttk.Button(frame, text="Publish", command=self.publish, state="disabled")
        self.publish_btn.grid(row=1, column=2, columnspan=3, pady=(10,0))
        
    def create_controls_frame(self):
        """Create control buttons frame"""
        frame = ttk.Frame(self.root)
        frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Button(frame, text="Clear Messages", command=self.clear_messages).pack(side="left", padx=(0,5))
        ttk.Button(frame, text="Export Messages", command=self.export_messages).pack(side="left", padx=(0,5))
        ttk.Button(frame, text="Database View", command=self.show_database_window).pack(side="left", padx=(0,5))
        ttk.Button(frame, text="Clear Database", command=self.clear_database).pack(side="left", padx=(0,20))
        
        self.toggle_scroll_btn = ttk.Button(frame, text="Disable Autoscroll", command=self.toggle_autoscroll)
        self.toggle_scroll_btn.pack(side="right")
        
        ttk.Label(frame, text="Filter:").pack(side="right", padx=(0,5))
        self.filter_entry = ttk.Entry(frame, width=20)
        self.filter_entry.pack(side="right", padx=(0,10))
        self.filter_entry.bind('<KeyRelease>', self.filter_messages)
        
    def create_messages_frame(self):
        """Create messages display frame"""
        frame = ttk.LabelFrame(self.root, text="📋 Messages", padding="5")
        frame.grid(row=4, column=0, padx=10, pady=(5,10), sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        self.messages = scrolledtext.ScrolledText(
            frame, height=15, wrap=tk.WORD,
            font=("Consolas", 9), bg="#f8f9fa"
        )
        self.messages.grid(row=0, column=0, sticky="nsew")
        
        # Configure text tags for colored output
        self.messages.tag_config("info", foreground="blue")
        self.messages.tag_config("error", foreground="red")
        self.messages.tag_config("success", foreground="green")
        self.messages.tag_config("topic", foreground="purple", font=("Consolas", 9, "bold"))
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            broker = self.broker.get().strip()
            port = int(self.port.get())
            username = self.username.get().strip() or None
            password = self.password.get().strip() or None
            
            if not broker:
                self.log_message("❌ Broker address required", "error")
                return
                
            # Save connection details
            self.save_to_file("brokers.json", broker)
            self.save_to_file("ports.json", str(port))
            self.refresh_comboboxes()
            
            # Disconnect existing client
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                
            # Create new client
            client_id = f'mqtt-explorer-{datetime.now().strftime("%H%M%S")}'
            self.client = mqtt.Client(client_id=client_id, clean_session=True)
            
            # Set authentication
            if username:
                self.client.username_pw_set(username, password)
                
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            self.client.on_log = self.on_log
            
            # SSL for port 8883
            if port == 8883:
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                self.client.tls_insecure_set(True)
                
            self.status_label.config(text="● Connecting...", foreground="orange")
            self.log_message(f"🔄 Connecting to {broker}:{port}...", "info")
            
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            
        except ValueError:
            self.log_message("❌ Invalid port number", "error")
        except Exception as e:
            self.log_message(f"❌ Connection failed: {str(e)}", "error")
            self.status_label.config(text="● Error", foreground="red")
            
    def disconnect(self):
        """Disconnect from broker"""
        if self.client and self.is_connected:
            self.client.disconnect()
        else:
            self.log_message("❌ Not connected", "error")
            
    def subscribe(self):
        """Subscribe to topic"""
        if not self.is_connected:
            self.log_message("❌ Not connected to broker", "error")
            return
            
        topic = self.topic.get().strip()
        qos = int(self.sub_qos.get())
        
        if not topic:
            self.log_message("❌ Topic required", "error")
            return
            
        self.save_to_file("topics.json", topic)
        self.refresh_comboboxes()
        
        self.client.subscribe(topic, qos)
        self.log_message(f"📥 Subscribed to {topic} (QoS {qos})", "success")
        
    def unsubscribe(self):
        """Unsubscribe from topic"""
        if not self.is_connected:
            self.log_message("❌ Not connected to broker", "error")
            return
            
        topic = self.topic.get().strip()
        if not topic or topic == "#":
            self.log_message("❌ Cannot unsubscribe from wildcard", "error")
            return
            
        self.client.unsubscribe(topic)
        self.log_message(f"📤 Unsubscribed from {topic}", "info")
        
    def publish(self):
        """Publish message"""
        if not self.is_connected:
            self.log_message("❌ Not connected to broker", "error")
            return
            
        topic = self.pub_topic.get().strip()
        message = self.pub_message.get()
        qos = int(self.pub_qos.get())
        retain = self.retain_var.get()
        
        if not topic:
            self.log_message("❌ Topic required", "error")
            return
            
        self.save_to_file("topics.json", topic)
        self.refresh_comboboxes()
        
        self.client.publish(topic, message, qos, retain)
        self.log_message(f"📤 Published to {topic}: {message} (QoS {qos}, Retain: {retain})", "success")
        self.pub_message.delete(0, tk.END)
        
    def on_connect(self, client, userdata, flags, rc):
        """Handle connection event"""
        if rc == 0:
            self.is_connected = True
            self.status_label.config(text="● Connected", foreground="green")
            self.log_message("✅ Connected successfully", "success")
            self.update_button_states()
        else:
            error_msgs = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier", 
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            error = error_msgs.get(rc, f"Unknown error ({rc})")
            self.log_message(f"❌ Connection refused: {error}", "error")
            self.status_label.config(text="● Error", foreground="red")
            
    def on_disconnect(self, client, userdata, rc):
        """Handle disconnection event"""
        self.is_connected = False
        self.status_label.config(text="● Disconnected", foreground="red")
        self.update_button_states()
        
        reason = "Clean disconnect" if rc == 0 else f"Unexpected disconnect ({rc})"
        self.log_message(f"🔌 Disconnected: {reason}", "info")
        
    def on_message(self, client, userdata, msg):
        """Handle received message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            message = msg.payload.decode('utf-8')
        except UnicodeDecodeError:
            message = f"<Binary: {msg.payload.hex()[:50]}...>"
            
        # Save to database
        self.save_message(timestamp, msg.topic, message, msg.qos)
        
        # Display in UI
        self.messages.insert('end', f"[{timestamp}] ", "info")
        self.messages.insert('end', f"{msg.topic}", "topic")
        self.messages.insert('end', f": {message}\n")
        
        if self.autoscroll_enabled:
            self.messages.see('end')
            
    def on_log(self, client, userdata, level, buf):
        """Handle MQTT client logs"""
        if level <= mqtt.MQTT_LOG_WARNING:
            self.log_message(f"🔧 {buf}", "info")
            
    def log_message(self, message, tag=""):
        """Log message to UI with optional formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.insert('end', f"[{timestamp}] {message}\n", tag)
        if self.autoscroll_enabled:
            self.messages.see('end')
            
    def save_message(self, timestamp, topic, message, qos=0):
        """Save message to database"""
        with self.db_lock:
            c = self.conn.cursor()
            c.execute("INSERT INTO messages (timestamp, topic, message, qos) VALUES (?,?,?,?)",
                     (timestamp, topic, message, qos))
            self.conn.commit()
            
    def update_button_states(self):
        """Update button states based on connection"""
        state = "normal" if self.is_connected else "disabled"
        alt_state = "disabled" if self.is_connected else "normal"
        
        self.subscribe_btn.config(state=state)
        self.unsubscribe_btn.config(state=state)
        self.publish_btn.config(state=state)
        self.connect_btn.config(state=alt_state)
        self.disconnect_btn.config(state=state)
        
    def save_to_file(self, filename, value):
        """Save value to JSON file"""
        filepath = f"./Storage/{filename}"
        try:
            data = self.load_from_file(filename) or []
            if value not in data:
                data.append(value)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            self.log_message(f"❌ Failed to save {filename}: {e}", "error")
            
    def load_from_file(self, filename):
        """Load data from JSON file"""
        filepath = f"./Storage/{filename}"
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
        
    def refresh_comboboxes(self):
        """Refresh all combobox values"""
        self.broker['values'] = self.load_from_file("brokers.json")
        self.port['values'] = self.load_from_file("ports.json")
        topics = self.load_from_file("topics.json")
        self.topic['values'] = topics
        self.pub_topic['values'] = topics
        
    def clear_messages(self):
        """Clear message display"""
        self.messages.delete('1.0', tk.END)
        self.log_message("🗑️ Messages cleared", "info")
        
    def clear_database(self):
        """Clear message database"""
        if messagebox.askyesno("Confirm", "Clear all stored messages?"):
            with self.db_lock:
                c = self.conn.cursor()
                c.execute("DELETE FROM messages")
                self.conn.commit()
            self.log_message("🗑️ Database cleared", "info")
            
    def export_messages(self):
        """Export messages to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")],
            title="Export Messages"
        )
        if filename:
            try:
                with self.db_lock:
                    c = self.conn.cursor()
                    c.execute("SELECT timestamp, topic, message, qos FROM messages ORDER BY id")
                    rows = c.fetchall()
                    
                data = [{"timestamp": r[0], "topic": r[1], "message": r[2], "qos": r[3]} for r in rows]
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                self.log_message(f"💾 Exported {len(data)} messages to {os.path.basename(filename)}", "success")
            except Exception as e:
                self.log_message(f"❌ Export failed: {e}", "error")
                
    def show_database_window(self):
        """Show database viewer window"""
        db_window = tk.Toplevel(self.root)
        db_window.title("Message Database")
        db_window.geometry("900x600")
        
        # Configure grid
        db_window.columnconfigure(0, weight=1)
        db_window.rowconfigure(1, weight=1)
        
        # Controls
        ctrl_frame = ttk.Frame(db_window)
        ctrl_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Button(ctrl_frame, text="Refresh", command=lambda: self.refresh_db_view(tree, count_lbl)).pack(side="left", padx=(0,5))
        ttk.Button(ctrl_frame, text="Export", command=self.export_messages).pack(side="left", padx=(0,20))
        
        count_lbl = ttk.Label(ctrl_frame, text="")
        count_lbl.pack(side="left")
        
        # Search
        ttk.Label(ctrl_frame, text="Search:").pack(side="right", padx=(20,5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(ctrl_frame, textvariable=search_var, width=20)
        search_entry.pack(side="right")
        search_var.trace('w', lambda *args: self.search_db(tree, search_var.get()))
        
        # Treeview
        tree = ttk.Treeview(db_window, columns=("Time", "Topic", "Message", "QoS"), show='headings')
        tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Configure columns
        tree.heading("Time", text="Timestamp")
        tree.heading("Topic", text="Topic")
        tree.heading("Message", text="Message") 
        tree.heading("QoS", text="QoS")
        
        tree.column("Time", width=80)
        tree.column("Topic", width=200)
        tree.column("Message", width=400)
        tree.column("QoS", width=50)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(db_window, orient="vertical", command=tree.yview)
        v_scroll.grid(row=1, column=1, sticky='ns')
        tree.configure(yscroll=v_scroll.set)
        
        # Load data
        self.refresh_db_view(tree, count_lbl)
        
    def refresh_db_view(self, tree, count_label):
        """Refresh database view"""
        for item in tree.get_children():
            tree.delete(item)
            
        with self.db_lock:
            c = self.conn.cursor()
            c.execute("SELECT timestamp, topic, message, qos FROM messages ORDER BY id DESC LIMIT 1000")
            rows = c.fetchall()
            
        for row in rows:
            tree.insert("", "end", values=row)
            
        count_label.config(text=f"Messages: {len(rows)}")
        
    def search_db(self, tree, search_term):
        """Search database entries"""
        if not search_term:
            self.refresh_db_view(tree, None)
            return
            
        for item in tree.get_children():
            tree.delete(item)
            
        with self.db_lock:
            c = self.conn.cursor()
            c.execute("""SELECT timestamp, topic, message, qos FROM messages 
                        WHERE topic LIKE ? OR message LIKE ? 
                        ORDER BY id DESC LIMIT 1000""", 
                     (f'%{search_term}%', f'%{search_term}%'))
            rows = c.fetchall()
            
        for row in rows:
            tree.insert("", "end", values=row)
            
    def filter_messages(self, event=None):
        """Filter displayed messages (placeholder)"""
        # This would require storing messages and re-displaying filtered ones
        pass
        
    def toggle_autoscroll(self):
        """Toggle autoscroll feature"""
        self.autoscroll_enabled = not self.autoscroll_enabled
        text = "Disable Autoscroll" if self.autoscroll_enabled else "Enable Autoscroll"
        self.toggle_scroll_btn.config(text=text)
        self.log_message(f"📜 Autoscroll {'enabled' if self.autoscroll_enabled else 'disabled'}", "info")
        
    def __del__(self):
        """Cleanup on exit"""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'client') and self.client:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTExplorer(root)
    root.mainloop()