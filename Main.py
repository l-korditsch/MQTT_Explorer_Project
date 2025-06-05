import tkinter as tk
from frontend import MQTTFrontend

# TODO Add auto scaling of HUD to window size
# TODO Prettefy the whole interface
# TODO add possibility to press enter in text fields to substitute button press

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTFrontend(root)
    root.mainloop()