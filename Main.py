import tkinter as tk
from frontend import MQTTFrontend

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTFrontend(root)
    root.mainloop()