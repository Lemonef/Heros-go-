import tkinter as tk
import multiprocessing
from visualizer.stats import StatsVisualizer

class SettingsWindow:
    def __init__(self, game, tk_root):
        self.game = game
        self.root = tk_root
        self.visualizer = None
        self.window = None


    def toggle_pause_gui(self, button):
        self.game.paused = not self.game.paused
        button.config(text="Resume Game" if self.game.paused else "Pause Game")

    def open_analytics(self):
        multiprocessing.Process(target=StatsVisualizer.launch_in_new_process).start()

    def quit_game(self, win):
        self.game.running = False
        win.destroy()
        
    def close_window(self):
        if self.window:
            self.window.destroy()
            self.window = None
        
    def run(self):
        if self.window and self.window.winfo_exists():
            self.close_window()
            return

        self.window = tk.Toplevel(self.root)
        self.window.title("Settings")
        self.window.geometry("250x260")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        pause_button = tk.Button(
            self.window,
            text="Resume Game" if self.game.paused else "Pause Game",
            command=lambda: self.toggle_pause_gui(pause_button)
        )
        pause_button.pack(pady=10)

        tk.Button(self.window, text="Show Stats", command=self.open_analytics).pack(pady=10)
        tk.Button(self.window, text="End Battle", command=lambda: self.quit_game(self.window)).pack(pady=10)
        tk.Button(self.window, text="Close", command=self.close_window).pack(pady=10)