import tkinter as tk
from tkinter import ttk, scrolledtext
import os
from datetime import datetime
from backend import MQTTBackend
from functools import partial


class MQTTFrontend:
    def __init__(self, root):
        """Initialize MQTT Explorer GUI"""
        self.root = root
        self.root.title("MQTT Explorer")

        # Test Style
        style = ttk.Style(root)
        style.theme_use("clam")

        # Configure main window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        # Initialize backend with callbacks
        self.backend = MQTTBackend(
            message_callback=self._on_message_received,
            status_callback=self._on_status_changed,
        )

        # UI state
        self.autoscroll_enabled = True
        self.subscribed_switch = False

        # Create UI components
        self._create_connection_frame()
        self._create_subscribe_frame()
        self._create_publish_frame()
        self._create_messages_frame()
        self._create_search_frame()  # <-- Add this line

    def _create_connection_frame(self):
        """Create connection settings frame"""
        self.conn_frame = ttk.LabelFrame(
            self.root, text="Connection Settings", padding="5"
        )
        self.conn_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.conn_frame.columnconfigure(1, weight=1)

        # Broker settings
        ttk.Label(self.conn_frame, text="Broker:").grid(row=0, column=0, padx=5, pady=5)
        self.broker = ttk.Combobox(self.conn_frame, width=30)
        self.broker["values"] = self.backend.load_brokers_from_file()
        self.broker.set("localhost")
        self.broker.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.conn_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5)
        self.port = ttk.Combobox(self.conn_frame, width=30)
        self.port["values"] = self.backend.load_ports_from_file()
        self.port.set("1883")
        self.port.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Status indicator
        self.status_label = ttk.Label(
            self.conn_frame, text="Status: Disconnected", foreground="red"
        )
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)

        # Connect button
        self.connect_btn = ttk.Button(
            self.conn_frame, text="Connect", command=self._connect
        )
        self.connect_btn.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

        # Disconnect button
        self.disconnect_btn = ttk.Button(
            self.conn_frame, text="Disconnect", command=self._disconnect
        )
        self.disconnect_btn.grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")
        self.broker.bind("<Return>", lambda e: self._focus(self.port))
        self.port.bind("<Return>", lambda e: self._connect())

    def _create_subscribe_frame(self):
        """Create subscribe frame"""
        self.sub_frame = ttk.LabelFrame(self.root, text="Subscribe", padding="5")
        self.sub_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.sub_frame.columnconfigure(1, weight=1)

        ttk.Label(self.sub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)

        # Combobox with existing topics
        self.topic = ttk.Combobox(self.sub_frame, width=30)
        self.topic["values"] = self.backend.load_topics_from_file()
        self.topic.set("#")
        self.topic.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Subscribe button
        self.subscribe_btn = ttk.Button(
            self.sub_frame, text="Subscribe", command=self._subscribe
        )
        self.subscribe_btn.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

        # Unsubscribe button
        self.unsubscribe_btn = ttk.Button(
            self.sub_frame, text="Unsubscribe", command=self._unsubscribe
        )
        self.unsubscribe_btn.grid(row=1, column=2, columnspan=2, pady=5, sticky="ew")
        self._bind_enter([self.topic], self._subscribe)

    def _create_publish_frame(self):
        """Create publish frame"""
        self.pub_frame = ttk.LabelFrame(self.root, text="Publish", padding="5")
        self.pub_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.pub_frame.columnconfigure(1, weight=1)

        ttk.Label(self.pub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        self.pub_topic = ttk.Combobox(self.pub_frame, width=30)
        self.pub_topic["values"] = self.backend.load_topics_from_file()
        self.pub_topic.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.pub_frame, text="Message:").grid(row=1, column=0, padx=5, pady=5)
        self.pub_message = ttk.Entry(self.pub_frame, width=30)
        self.pub_message.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.publish_btn = ttk.Button(
            self.pub_frame, text="Publish", command=self._publish
        )
        self.publish_btn.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        self._bind_enter([self.pub_topic, self.pub_message], self._publish)
        self.pub_topic.bind("<Return>", lambda e: self._focus(self.pub_message))
        self.pub_message.bind("<Return>", lambda e: self._publish())

    def _create_messages_frame(self):
        """Create messages frame"""
        self.msg_frame = ttk.LabelFrame(self.root, text="Messages", padding="5")
        self.msg_frame.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
        self.msg_frame.rowconfigure(0, weight=1)
        self.msg_frame.columnconfigure(0, weight=1)

        # Button frame for message controls
        self.msg_btn_frame = ttk.Frame(self.msg_frame)
        self.msg_btn_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        for i in range(5):
            self.msg_btn_frame.columnconfigure(i, weight=1)

        self.clear_msg_btn = ttk.Button(
            self.msg_btn_frame, text="Clear Messages", command=self._clear_messages
        )
        self.clear_msg_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.clear_db_btn = ttk.Button(
            self.msg_btn_frame, text="Clear Database", command=self._clear_database
        )
        self.clear_db_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.show_db_btn = ttk.Button(
            self.msg_btn_frame, text="Show Database", command=self._show_database_window
        )
        self.show_db_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.show_db_ui_btn = ttk.Button(
            self.msg_btn_frame,
            text="Show recent messages",
            command=self._show_database_in_ui,
        )
        self.show_db_ui_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.toggle_scroll_btn = ttk.Button(
            self.msg_btn_frame,
            text="Disable Autoscroll",
            command=self._toggle_autoscroll,
        )
        self.toggle_scroll_btn.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        self.messages = scrolledtext.ScrolledText(self.msg_frame, height=10, width=100)
        self.messages.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Tracking to display messages
        self.messages.bind("<MouseWheel>", self.check_scroll_position)
        self.messages.bind("<Button-4>", self.check_scroll_position)
        self.messages.bind("<Button-5>", self.check_scroll_position)
        self.messages.bind("<KeyRelease>", self.check_scroll_position)
        self.messages.bind("<Motion>", self.check_scroll_position)

    def _create_search_frame(self):
        """Create search frame for topics and messages"""
        self.search_frame = ttk.LabelFrame(self.root, text="Search", padding="5")
        self.search_frame.grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        self.search_frame.columnconfigure(1, weight=1)

        ttk.Label(self.search_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = ttk.Entry(self.search_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self._search_messages())

        self.search_btn = ttk.Button(
            self.search_frame, text="Search", command=self._search_messages
        )
        self.search_btn.grid(row=0, column=2, padx=5, pady=5)

        self.clear_search_btn = ttk.Button(
            self.search_frame, text="Clear Search", command=self._clear_search
        )
        self.clear_search_btn.grid(row=0, column=3, padx=5, pady=5)

    def _connect(self):
        """Handle connect button click"""
        broker = self.broker.get()
        try:
            port = int(self.port.get())
        except ValueError:
            self._log_message("Error: Invalid port number")
            return

        if port == 42:
            import tkinter.messagebox

            tkinter.messagebox.showinfo(
                "Easter Egg",
                "42 ist die Antwort auf alles – aber vielleicht nicht der beste MQTT-Port 😉",
            )

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
            # Reset subscription state when disconnecting
            self.subscribed_switch = False
            self.backend.clear_current_topic()
        else:
            self._log_message("Error: Not connected to broker")

    def _subscribe(self):
        """Handle subscribe button click"""
        topic = self.topic.get()

        # Unsubscribe from previous topic if already subscribed
        if self.subscribed_switch:
            current_topic = self.backend.get_current_topic()
            if current_topic:
                self.backend.unsubscribe(current_topic)
                self._log_message(f"Unsubscribed from previous topic: {current_topic}")

        # Store and subscribe to new topic
        if self.backend.store_topic_to_file(topic):
            self._refresh_topic_comboboxes()
        if self.backend.subscribe(topic):
            self._log_message(f"Subscribed to {topic}")
            self.subscribed_switch = True
        else:
            self._log_message(f"Failed to subscribe to {topic}")
            self.subscribed_switch = False

    def _unsubscribe(self):
        """Handle unsubscribe button click"""
        # Get the current topic from the backend if available
        current_topic = self.backend.get_current_topic()

        # If no current topic, use the topic from the UI
        topic_to_unsubscribe = current_topic if current_topic else self.topic.get()

        if self.backend.unsubscribe(topic_to_unsubscribe):
            self._log_message(f"Unsubscribed from {topic_to_unsubscribe}")
            # Reset the subscribed state
            self.subscribed_switch = False
        else:
            self._log_message(f"Failed to unsubscribe from {topic_to_unsubscribe}")

    def _publish(self):
        """Handle publish button click"""
        topic = self.pub_topic.get()
        message = self.pub_message.get()

        if "antwort auf alles" in message.lower():
            import tkinter.messagebox

            tkinter.messagebox.showinfo(
                "42",
                "Die Antwort auf die ultimative Frage des Lebens, des Universums und allem ist: 42",
            )

        if self.backend.publish(topic, message):
            self._log_message(f"Published to {topic}: {message}")

    def _clear_messages(self):
        """Clear messages display"""
        self.messages.delete("1.0", tk.END)

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
        refresh_btn = ttk.Button(
            control_frame,
            text="Refresh",
            command=lambda: self._refresh_database_view(tree, count_label),
        )
        refresh_btn.grid(row=0, column=0, padx=5, pady=5)

        # Add export button
        export_btn = ttk.Button(
            control_frame, text="Export to File", command=self._export_database
        )
        export_btn.grid(row=0, column=1, padx=5, pady=5)

        # Add count label
        count_label = ttk.Label(control_frame, text="")
        count_label.grid(row=0, column=2, padx=20, pady=5)
        tree = ttk.Treeview(
            db_window,
            columns=("Timestamp", "Direction", "Topic", "Message"),
            show="headings",
        )
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Direction", text="Direction")
        tree.heading("Topic", text="Topic")
        tree.heading("Message", text="Message")

        # Configure column widths
        tree.column("Timestamp", width=100)
        tree.column("Direction", width=80)
        tree.column("Topic", width=200)
        tree.column("Message", width=350)

        tree.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(db_window, orient="vertical", command=tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscroll=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(db_window, orient="horizontal", command=tree.xview)
        h_scrollbar.grid(row=2, column=0, sticky="ew")
        tree.configure(xscroll=h_scrollbar.set)

        # Load initial data
        self._refresh_database_view(tree, count_label)

    def _refresh_database_view(self, tree, count_label=None):
        """Refresh the database view with current data"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)  # Insert data into the treeview
        try:
            rows = self.backend.get_database().get_all_messages()
            for row in rows:
                # Reorder columns: (timestamp, topic, message, direction) -> (timestamp, direction, topic, message)
                if len(row) == 4:
                    timestamp, topic, message, direction = row
                    reordered_row = (timestamp, direction, topic, message)
                    tree.insert("", "end", values=reordered_row)
                else:
                    # Handle case where direction column might not exist (backward compatibility)
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

            self._log_message("\n--- Recent Database Entries ---\n", False)
            for row in rows:
                if len(row) == 4:
                    # New format with direction
                    timestamp, topic, message, direction = row
                    self._log_message(
                        f"[{timestamp}] {direction } {topic}: {message}",
                        False,
                        True,
                    )
                else:
                    # Old format without direction (backward compatibility)
                    timestamp, topic, message = row
                    self._log_message(f"[{timestamp}] {topic}: {message}", False, True)
            self._log_message("--- End Database Entries ---\n", False)

        except Exception as e:
            self._log_message(f"Failed to show database: {e}")

    def _toggle_autoscroll(self):
        """Toggle autoscroll functionality"""
        self.autoscroll_enabled = not self.autoscroll_enabled
        new_label = (
            "Disable Autoscroll" if self.autoscroll_enabled else "Enable Autoscroll"
        )
        self.toggle_scroll_btn.config(text=new_label)
        self._log_message(
            f"Autoscroll {'enabled' if self.autoscroll_enabled else 'disabled'}"
        )

    def check_scroll_position(self, event=None):
        # Get current position
        top, bottom = self.messages.yview()

        # If near the bottom (5%), enable autoscroll
        if bottom >= 0.99:
            if not self.autoscroll_enabled:
                self.autoscroll_enabled = True
                self.toggle_scroll_btn.config(text="Disable Autoscroll")
                self._log_message("Autoscroll re-enabled (user at bottom)")
        else:
            if self.autoscroll_enabled:
                self.autoscroll_enabled = False
                self.toggle_scroll_btn.config(text="Enable Autoscroll")
                self._log_message("Autoscroll disabled (user scrolled)")

    def _focus(self, widget, _event=None):
        """Move keyboard focus to *widget*."""
        widget.focus_set()

    def _log_message(self, message, show_time=True, show_date=False):
        """Log message to UI"""
        if show_time:
            if show_date:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                current_time = datetime.now().strftime("%H:%M:%S")
            self.messages.insert("end", f"[{current_time}] {message}\n")
        else:
            self.messages.insert("end", f"{message}\n")
        if self.autoscroll_enabled:
            self.messages.see("end")

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
            # Reset subscription state when disconnected
            self.subscribed_switch = False
            self.backend.clear_current_topic()
        elif status == "error":
            self.status_label.config(text="Status: Error", foreground="red")
            self._log_message(message)

    def _bind_enter(self, widgets, callback):
        """Bind the Return key on every widget in *widgets* to *callback*."""
        for w in widgets:
            w.bind("<Return>", partial(self._invoke_from_event, callback))

    def _invoke_from_event(self, callback, _event):
        """Wrapper so Tkinter passes the event obj but we ignore it."""
        callback()

    def _refresh_broker_combobox(self):
        """Refresh broker combobox values"""
        brokers = self.backend.load_brokers_from_file()
        self.broker["values"] = brokers

    def _refresh_port_combobox(self):
        """Refresh port combobox values"""
        ports = self.backend.load_ports_from_file()
        self.port["values"] = ports

    def _refresh_topic_comboboxes(self):
        """Refresh topic combobox values"""
        topics = self.backend.load_topics_from_file()
        self.topic["values"] = topics
        self.pub_topic["values"] = topics

    def close(self):
        """Close the application"""
        self.backend.close()

    def __del__(self):
        """Cleanup on exit"""
        self.close()

    def _search_messages(self):
        """Search for topics or messages in the displayed messages"""
        query = self.search_entry.get().strip().lower()
        if not query:
            return

        # Get all text from the messages widget
        all_text = self.messages.get("1.0", tk.END)
        lines = all_text.splitlines()

        # Filter lines that contain the query
        results = [line for line in lines if query in line.lower()]

        # Show results in the messages widget
        self.messages.delete("1.0", tk.END)
        if results:
            for line in results:
                self.messages.insert(tk.END, line + "\n")
            self._log_message(f"Search results for '{query}': {len(results)} found", show_time=False)
        else:
            self._log_message(f"No results found for '{query}'", show_time=False)

    def _clear_search(self):
        """Clear search and show all messages again (if you want to reload from DB, adapt here)"""
        self.messages.delete("1.0", tk.END)
        self._log_message("Search cleared. Only new messages will be shown.", show_time=False)
