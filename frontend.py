import tkinter as tk
from tkinter import ttk, scrolledtext
import os
from datetime import datetime
from backend import MQTTBackend


class MQTTFrontend:
    def __init__(self, root):
        """Initialize MQTT Explorer GUI"""
        self.root = root
        self.root.title("MQTT Explorer")
        
        # Configure main window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # Initialize backend with callbacks
        self.backend = MQTTBackend(
            message_callback=self._on_message_received,
            status_callback=self._on_status_changed
        )
        
        # UI state
        self.autoscroll_enabled = True
        self.subscribed_switch = False
        
        # Create UI components
        self._create_connection_frame()
        self._create_subscribe_frame()
        self._create_publish_frame()
        self._create_messages_frame()
    
    def _create_connection_frame(self):
        """Create connection settings frame"""
        self.conn_frame = ttk.LabelFrame(self.root, text="Connection Settings", padding="5")
        self.conn_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Broker settings
        ttk.Label(self.conn_frame, text="Broker:").grid(row=0, column=0, padx=5, pady=5)
        self.broker = ttk.Combobox(self.conn_frame, width=30)
        self.broker['values'] = self.backend.load_brokers_from_file()
        self.broker.set("localhost")
        self.broker.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.conn_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5)
        self.port = ttk.Combobox(self.conn_frame, width=30)
        self.port['values'] = self.backend.load_ports_from_file()
        self.port.set("1883")
        self.port.grid(row=1, column=1, padx=5, pady=5)
        
        # Status indicator
        self.status_label = ttk.Label(self.conn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Connect button
        self.connect_btn = ttk.Button(self.conn_frame, text="Connect", command=self._connect)
        self.connect_btn.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Disconnect button
        self.disconnect_btn = ttk.Button(self.conn_frame, text="Disconnect", command=self._disconnect)
        self.disconnect_btn.grid(row=4, column=0, columnspan=2, pady=5)
    
    def _create_subscribe_frame(self):
        """Create subscribe frame"""
        self.sub_frame = ttk.LabelFrame(self.root, text="Subscribe", padding="5")
        self.sub_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(self.sub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        
        # Combobox with existing topics
        self.topic = ttk.Combobox(self.sub_frame, width=30)
        self.topic['values'] = self.backend.load_topics_from_file()
        self.topic.set("#")
        self.topic.grid(row=0, column=1, padx=5, pady=5)
        
        # Subscribe button
        self.subscribe_btn = ttk.Button(self.sub_frame, text="Subscribe", command=self._subscribe)
        self.subscribe_btn.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Unsubscribe button
        self.unsubscribe_btn = ttk.Button(self.sub_frame, text="Unsubscribe", command=self._unsubscribe)
        self.unsubscribe_btn.grid(row=1, column=2, columnspan=2, pady=5)
    
    def _create_publish_frame(self):
        """Create publish frame"""
        self.pub_frame = ttk.LabelFrame(self.root, text="Publish", padding="5")
        self.pub_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(self.pub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        self.pub_topic = ttk.Combobox(self.pub_frame, width=30)
        self.pub_topic['values'] = self.backend.load_topics_from_file()
        self.pub_topic.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.pub_frame, text="Message:").grid(row=1, column=0, padx=5, pady=5)
        self.pub_message = ttk.Entry(self.pub_frame, width=30)
        self.pub_message.grid(row=1, column=1, padx=5, pady=5)
        
        self.publish_btn = ttk.Button(self.pub_frame, text="Publish", command=self._publish)
        self.publish_btn.grid(row=2, column=0, columnspan=2, pady=5)
    
    def _create_messages_frame(self):
        """Create messages frame"""
        self.msg_frame = ttk.LabelFrame(self.root, text="Messages", padding="5")
        self.msg_frame.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
        
        # Button frame for message controls
        self.msg_btn_frame = ttk.Frame(self.msg_frame)
        self.msg_btn_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.clear_msg_btn = ttk.Button(self.msg_btn_frame, text="Clear Messages", command=self._clear_messages)
        self.clear_msg_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.clear_db_btn = ttk.Button(self.msg_btn_frame, text="Clear Database", command=self._clear_database)
        self.clear_db_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.show_db_btn = ttk.Button(self.msg_btn_frame, text="Show Database", command=self._show_database_window)
        self.show_db_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.show_db_ui_btn = ttk.Button(self.msg_btn_frame, text="Show DB in UI", command=self._show_database_in_ui)
        self.show_db_ui_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.toggle_scroll_btn = ttk.Button(
            self.msg_btn_frame,
            text="Disable Autoscroll",
            command=self._toggle_autoscroll
        )
        self.toggle_scroll_btn.grid(row=0, column=4, padx=5, pady=5)
        
        self.messages = scrolledtext.ScrolledText(self.msg_frame, height=10, width=100)
        self.messages.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    
    def _connect(self):
        """Handle connect button click"""
        broker = self.broker.get()
        try:
            port = int(self.port.get())
        except ValueError:
            self._log_message("Error: Invalid port number")
            return
        
        # Store connection details
        if self.backend.store_port_to_file(str(port)):
            self._refresh_port_combobox()
        
        if self.backend.store_broker_to_file(broker):
            self._refresh_broker_combobox()
        
        # Update status
        self.status_label.config(text="Status: Connecting...", foreground="orange")
        self._log_message(f"Connecting to {broker}:{port}...")
        
        # Try to connect
        success = self.backend.connect(broker, port)
        if not success:
            self.status_label.config(text="Status: Error", foreground="red")
    
    def _disconnect(self):
        """Handle disconnect button click"""
        if self.backend.disconnect():
            self._log_message("Disconnected from broker")
        else:
            self._log_message("Error: Not connected to broker")
    
    def _subscribe(self):
        """Handle subscribe button click"""
        topic = self.topic.get()
        
        # Unsubscribe from previous topic if needed
        try:
            topics = self.backend.load_topics_from_file()
            if isinstance(topics, list) and len(topics) > 0 and self.subscribed_switch:
                last_topic = topics[-1]
                self.backend.unsubscribe(last_topic)
        except Exception:
            pass
        
        # Store and subscribe to new topic
        if self.backend.store_topic_to_file(topic):
            self._refresh_topic_comboboxes()
        
        if self.backend.subscribe(topic):
            self._log_message(f"Subscribed to {topic}")
            self.subscribed_switch = True
    
    def _unsubscribe(self):
        """Handle unsubscribe button click"""
        topic = self.topic.get()
        if self.backend.unsubscribe(topic):
            self._log_message(f"Unsubscribed from {topic}")
    
    def _publish(self):
        """Handle publish button click"""
        topic = self.pub_topic.get()
        message = self.pub_message.get()
        
        if self.backend.publish(topic, message):
            self._log_message(f"Published to {topic}: {message}")
    
    def _clear_messages(self):
        """Clear messages display"""
        self.messages.delete('1.0', tk.END)
    
    def _clear_database(self):
        """Clear the messages database"""
        try:
            self.backend.get_database().clear_database()
            self._log_message("Database cleared")
        except Exception as e:
            self._log_message(f"Error clearing database: {e}")
    
    def _show_database_window(self):
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
        refresh_btn = ttk.Button(control_frame, text="Refresh", 
                                command=lambda: self._refresh_database_view(tree, count_label))
        refresh_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Add export button
        export_btn = ttk.Button(control_frame, text="Export to File", command=self._export_database)
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
        self._refresh_database_view(tree, count_label)
    
    def _refresh_database_view(self, tree, count_label=None):
        """Refresh the database view with current data"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Insert data into the treeview
        try:
            rows = self.backend.get_database().get_all_messages()
            for row in rows:
                tree.insert("", "end", values=row)
            
            # Update count if label provided
            if count_label:
                count_label.config(text=f"Total messages: {len(rows)}")
        except Exception as e:
            self._log_message(f"Error refreshing database view: {e}")
    
    def _export_database(self):
        """Export database contents to a JSON file"""
        try:
            filepath = self.backend.get_database().export_to_json()
            filename = os.path.basename(filepath)
            self._log_message(f"Database exported to {filename}")
        except Exception as e:
            self._log_message(f"Failed to export database: {e}")
    
    def _show_database_in_ui(self):
        """Show recent database entries in the main UI"""
        try:
            rows = self.backend.get_database().get_recent_messages(10)
            
            self._log_message("--- Recent Database Entries ---")
            for row in rows:
                timestamp, topic, message = row
                self._log_message(f"[{timestamp}] {topic}: {message}")
            self._log_message("--- End Database Entries ---")
            
        except Exception as e:
            self._log_message(f"Failed to show database: {e}")
    
    def _toggle_autoscroll(self):
        """Toggle autoscroll functionality"""
        self.autoscroll_enabled = not self.autoscroll_enabled
        new_label = "Disable Autoscroll" if self.autoscroll_enabled else "Enable Autoscroll"
        self.toggle_scroll_btn.config(text=new_label)
        self._log_message(f"Autoscroll {'enabled' if self.autoscroll_enabled else 'disabled'}")
    
    def _log_message(self, message):
        """Log message to UI"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.insert('end', f"[{current_time}] {message}\n")
        if self.autoscroll_enabled:
            self.messages.see('end')
    
    def _on_message_received(self, topic, message, timestamp):
        """Callback for when a message is received"""
        self._log_message(f"{topic}: {message}")
    
    def _on_status_changed(self, status, message):
        """Callback for when connection status changes"""
        if status == "connected":
            self.status_label.config(text="Status: Connected", foreground="green")
            self._log_message(message)
        elif status == "disconnected":
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self._log_message(message)
        elif status == "error":
            self.status_label.config(text="Status: Error", foreground="red")
            self._log_message(message)
    
    def _refresh_broker_combobox(self):
        """Refresh broker combobox values"""
        brokers = self.backend.load_brokers_from_file()
        self.broker['values'] = brokers
    
    def _refresh_port_combobox(self):
        """Refresh port combobox values"""
        ports = self.backend.load_ports_from_file()
        self.port['values'] = ports
    
    def _refresh_topic_comboboxes(self):
        """Refresh topic combobox values"""
        topics = self.backend.load_topics_from_file()
        self.topic['values'] = topics
        self.pub_topic['values'] = topics
    
    def close(self):
        """Close the application"""
        self.backend.close()
    
    def __del__(self):
        """Cleanup on exit"""
        self.close()
