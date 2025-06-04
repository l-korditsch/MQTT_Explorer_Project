import paho.mqtt.client as mqtt
import ssl
import json
import os
from datetime import datetime
from database import MQTTDatabase


class MQTTBackend:
    def __init__(self, message_callback=None, status_callback=None):
        """Initialize MQTT backend"""
        self.client = None
        self.database = MQTTDatabase()
        self.message_callback = message_callback
        self.status_callback = status_callback
        self.subscribed_topics = set()
        self.current_topic = None  # Track currently subscribed topic

        # Ensure storage folder exists
        os.makedirs("./Storage/", exist_ok=True)

    def connect(self, broker, port):
        """Connect to MQTT broker"""
        try:
            # Disconnect existing client if any
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()

            # Create new client instance with clean session
            client_id = f'python-mqtt-{datetime.now().strftime("%H%M%S")}'
            self.client = mqtt.Client(client_id=client_id, clean_session=True)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect

            # Try SSL for secure connection if using port 8883
            if port == 8883:
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                self.client.tls_insecure_set(True)

            # Increase timeouts for more stability
            self.client._connect_timeout = 30
            self.client._keepalive = 60

            # Try to connect
            self.client.connect(broker, port)
            self.client.loop_start()

            return True

        except Exception as e:
            if self.status_callback:
                self.status_callback("error", f"Connection failed: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from the broker"""
        if self.client and self.client.is_connected():
            self.client.disconnect()
            return True
        return False

    def subscribe(self, topic):
        """Subscribe to a topic"""
        if not self.client or not self.client.is_connected():
            if self.status_callback:
                self.status_callback("error", "Not connected to broker")
            return False

        self.client.subscribe(topic)
        self.subscribed_topics.add(topic)
        self.current_topic = topic  # Track current topic
        return True

    def unsubscribe(self, topic):
        """Unsubscribe from a topic"""
        if not self.client or not self.client.is_connected():
            if self.status_callback:
                self.status_callback("error", "Not connected to broker")
            return False

        # If no specific topic provided, unsubscribe from current topic
        if not topic and self.current_topic:
            topic = self.current_topic

        if topic == "#":
            # For wildcard topics, disconnect to properly unsubscribe
            self.disconnect()
            if self.status_callback:
                self.status_callback(
                    "disconnected", "Disconnected to unsubscribe from wildcard topic"
                )
            self.current_topic = None
            return True

        self.client.unsubscribe(topic)
        self.subscribed_topics.discard(topic)

        # Clear current topic if we unsubscribed from it
        if topic == self.current_topic:
            self.current_topic = None

        return True

    def publish(self, topic, message):
        """Publish a message to a topic"""
        if not self.client or not self.client.is_connected():
            if self.status_callback:
                self.status_callback("error", "Not connected to broker")
            return False

        self.client.publish(topic, message)
        return True

    def is_connected(self):
        """Check if client is connected"""
        return self.client and self.client.is_connected()

    def _on_connect(self, client, userdata, flags, rc):
        """Handle connection callback"""
        if rc == 0:
            if self.status_callback:
                self.status_callback("connected", "Connected successfully")
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized",
            }
            error = error_messages.get(rc, f"Connection failed with code {rc}")
            if self.status_callback:
                self.status_callback("error", error)

    def _on_disconnect(self, client, userdata, rc):
        """Handle disconnect callback"""
        disconnect_reasons = {
            0: "Clean disconnect",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized",
            6: "Connection lost",
            7: "Connection timed out or network error",
        }
        reason = disconnect_reasons.get(rc, f"Unknown error (code={rc})")
        if self.status_callback:
            self.status_callback("disconnected", f"Disconnected: {reason}")

    def _on_message(self, client, userdata, msg):
        """Handle received messages"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Attempt to decode the payload as UTF-8
            message = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            # Handle non-UTF-8 payloads
            message = f"<Binary Data: {msg.payload.hex()}>"

        # Save to database
        self.database.save_message(current_time, msg.topic, message)

        # Call message callback if provided
        if self.message_callback:
            self.message_callback(msg.topic, message, current_time)

    def store_broker_to_file(self, broker, filename="brokers.txt"):
        """Store broker to file"""
        if not broker:
            return False

        try:
            filepath = os.path.join("./Storage/", filename)

            # Load existing brokers from file
            if os.path.exists(filepath):
                with open(filepath, "r") as file:
                    try:
                        brokers = json.load(file)
                    except json.JSONDecodeError:
                        brokers = []
            else:
                brokers = []

            # Save new broker if not already in list
            if broker not in brokers:
                brokers.append(broker)
                with open(filepath, "w") as file:
                    json.dump(brokers, file, indent=2)
                return True

            return False

        except Exception:
            return False

    def load_brokers_from_file(self, filename="brokers.txt"):
        """Load brokers from file"""
        filepath = os.path.join("./Storage/", filename)
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r") as file:
                brokers = json.load(file)
                return brokers if isinstance(brokers, list) else []
        except Exception:
            return []

    def store_port_to_file(self, port, filename="ports.txt"):
        """Store port to file"""
        if not port:
            return False

        try:
            filepath = os.path.join("./Storage/", filename)

            if os.path.exists(filepath):
                with open(filepath, "r") as file:
                    try:
                        ports = json.load(file)
                    except json.JSONDecodeError:
                        ports = []
            else:
                ports = []

            if port not in ports:
                ports.append(port)
                with open(filepath, "w") as file:
                    json.dump(ports, file, indent=2)
                return True

            return False

        except Exception:
            return False

    def load_ports_from_file(self, filename="ports.txt"):
        """Load ports from file"""
        filepath = os.path.join("./Storage/", filename)
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r") as file:
                ports = json.load(file)
                return ports if isinstance(ports, list) else []
        except Exception:
            return []

    def store_topic_to_file(self, topic, filename="topics.txt"):
        """Store topic to file"""
        if not topic:
            return False

        try:
            filepath = os.path.join("./Storage/", filename)

            # Load existing topics from JSON file, or start a new list
            if os.path.exists(filepath):
                with open(filepath, "r") as file:
                    try:
                        topics = json.load(file)
                    except json.JSONDecodeError:
                        topics = []
            else:
                topics = []

            # Add the topic if not already present
            if topic not in topics:
                topics.append(topic)
                with open(filepath, "w") as file:
                    json.dump(topics, file, indent=2)
                return True

            return False

        except Exception:
            return False

    def load_topics_from_file(self, filename="topics.txt"):
        """Load topics from file"""
        filepath = os.path.join("./Storage/", filename)
        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, "r") as file:
                topics = json.load(file)
                if isinstance(topics, list):
                    return topics
                else:
                    return []
        except (json.JSONDecodeError, Exception):
            return []

    def get_database(self):
        """Get database instance"""
        return self.database

    def close(self):
        """Close backend connections"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        if self.database:
            self.database.close()

    def __del__(self):
        """Cleanup on exit"""
        self.close()

    def get_current_topic(self):
        """Get the currently subscribed topic"""
        return self.current_topic

    def clear_current_topic(self):
        """Clear the current topic tracking"""
        self.current_topic = None
