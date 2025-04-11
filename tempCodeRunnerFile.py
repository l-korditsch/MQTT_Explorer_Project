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