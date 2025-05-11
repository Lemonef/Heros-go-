import tkinter as tk
from tkinter import ttk
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatsVisualizer:
    def __init__(self, csv_path="game_data.csv", parent=None):
        self.csv_path = csv_path
        self.df = None
        self.parent = parent
        self.root = None
        self.status_label = None

    @staticmethod
    def launch_in_new_process():
        from visualizer import StatsVisualizer
        vis = StatsVisualizer()
        vis.show()

    def moving_average(self, data, window_size=3):
        return pd.Series(data).rolling(window=window_size, min_periods=1).mean()

    def show(self):
        self.root = tk.Tk()
        self.root.title("Battle Heroes Defense Analytics")
        self.root.geometry("1000x600")

        self.status_label = ttk.Label(self.root, text="Loading stats...", anchor='center')
        self.status_label.pack(expand=True)

        self.root.after(10, self._build_ui_async)
        self.root.mainloop()

    def _build_ui_async(self):
        self.status_label.destroy()
        self.df = pd.read_csv(self.csv_path)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        self._plot_enemies_vs_heroes(notebook)
        self._plot_energy(notebook)
        self._plot_abilities(notebook)
        self._plot_most_spawned(notebook)

        ttk.Button(self.root, text="Close", command=self.root.destroy).pack(pady=10)

    def _plot_enemies_vs_heroes(self, notebook):
        frame = ttk.Frame(notebook)
        fig, ax = plt.subplots()
        ax.plot(self.df['EnemiesDefeated'], label='Enemies Defeated')
        ax.plot(self.df['HeroesDefeated'], label='Heroes Defeated')
        ax.set_title('Enemies vs Heroes Defeated')
        ax.legend()
        FigureCanvasTkAgg(fig, frame).get_tk_widget().pack(fill='both', expand=True)
        notebook.add(frame, text="Enemies vs Heroes")

    def _plot_energy(self, notebook):
        frame = ttk.Frame(notebook)
        fig, ax = plt.subplots()
        ax.plot(self.df['TotalEnergyUsed'], color='tab:blue')
        ax.set_title('Total Energy Used Over Time')
        FigureCanvasTkAgg(fig, frame).get_tk_widget().pack(fill='both', expand=True)
        notebook.add(frame, text="Energy Usage")

    def _plot_abilities(self, notebook):
        frame = ttk.Frame(notebook)
        fig, ax = plt.subplots()
        ax.plot(self.moving_average(self.df['Attack_speed_Buff_Used']), label='Buff')
        ax.plot(self.moving_average(self.df['AOE_Used']), label='AOE')
        ax.plot(self.moving_average(self.df['GroupHeal_Used']), label='Heal')
        ax.set_title('Ability Usage Over Time')
        ax.legend()
        FigureCanvasTkAgg(fig, frame).get_tk_widget().pack(fill='both', expand=True)
        notebook.add(frame, text="Ability Usage")

    def _plot_most_spawned(self, notebook):
        frame = ttk.Frame(notebook)
        fig, ax = plt.subplots()
        df_non_none = self.df[self.df['MostSpawnedHero'] != 'None']
        sns.stripplot(data=df_non_none, x=df_non_none.index, y='MostSpawnedHero', ax=ax, jitter=True, size=5)
        ax.set_title('Most Spawned Hero Over Time')
        FigureCanvasTkAgg(fig, frame).get_tk_widget().pack(fill='both', expand=True)
        notebook.add(frame, text="Most Spawned Hero")
