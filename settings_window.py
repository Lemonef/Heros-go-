import tkinter as tk
from visualizer import StatsVisualizer
import multiprocessing

class SettingsWindow:
    def __init__(self, game, tk_root):
        self.game = game
        self.root = tk_root
        self.visualizer = None

    def toggle_pause_gui(self, button):
        self.game.paused = not self.game.paused
        button.config(
            text="Resume Game" if self.game.paused else "Pause Game"
        )

    def open_analytics(self):
        multiprocessing.Process(target=StatsVisualizer.launch_in_new_process).start()


    def quit_game(self, win):
        self.game.running = False
        win.destroy()

    def run(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("250x220")

        pause_button = tk.Button(
            win,
            text="Resume Game" if self.game.paused else "Pause Game",
            command=lambda: self.toggle_pause_gui(pause_button)
        )
        pause_button.pack(pady=10)

        tk.Button(win, text="Show Stats", command=self.open_analytics).pack(pady=10)
        tk.Button(win, text="Quit Game", command=lambda: self.quit_game(win)).pack(pady=10)
