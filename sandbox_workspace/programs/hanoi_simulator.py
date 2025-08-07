import tkinter as tk
from tkinter import messagebox
import time

class HanoiSimulator:
    def __init__(self, root, num_disks, num_towers):
        self.root = root
        self.num_disks = num_disks
        self.num_towers = num_towers
        self.tower_width = 50
        self.tower_height = 300
        self.disk_height = 20
        self.disk_width = 20
        self.spacing = 100
        self.tower_positions = [0, self.spacing, 2 * self.spacing]
        self.disk_colors = ["red", "orange", "yellow", "green", "blue", "purple", "cyan", "magenta", "lime", "pink"]
        self.canvas = tk.Canvas(root, width=800, height=600, bg="black")
        self.canvas.pack()
        self.towers = [[] for _ in range(self.num_towers)]
        self.draw_towers()
        self.solve_hanoi(self.num_disks, 0, self.num_towers - 1, 1)

    def draw_towers(self):
        for i in range(self.num_towers):
            x = self.tower_positions[i]
            self.canvas.create_rectangle(x, 0, x + self.tower_width, self.tower_height, fill="gray", outline="black")

    def draw_disks(self):
        self.canvas.delete("disk")
        for tower in self.towers:
            y = self.tower_height - self.disk_height
            for disk in tower:
                width = self.disk_width * (disk + 1)
                color = self.disk_colors[disk]
                self.canvas.create_rectangle(
                    self.tower_positions[self.towers.index(tower)] - width // 2,
                    y,
                    self.tower_positions[self.towers.index(tower)] + width // 2,
                    y + self.disk_height,
                    fill=color, outline="black", tags="disk"
                )
                y -= self.disk_height + 5

    def solve_hanoi(self, n, source, target, auxiliary):
        if n == 1:
            self.move_disk(source, target)
        else:
            self.solve_hanoi(n - 1, source, auxiliary, target)
            self.move_disk(source, target)
            self.solve_hanoi(n - 1, auxiliary, target, source)

    def move_disk(self, source, target):
        disk = self.towers[source].pop()
        self.towers[target].append(disk)
        self.draw_disks()
        self.root.update()
        time.sleep(0.5)

def main():
    root = tk.Tk()
    root.title("Tower of Hanoi Simulator")
    root.geometry("800x600")
    root.resizable(False, False)

    def start_simulation():
        try:
            num_disks = int(num_disks_entry.get())
            num_towers = int(num_towers_entry.get())
            if 3 <= num_towers <= 15 and 1 <= num_disks <= num_towers:
                HanoiSimulator(root, num_disks, num_towers)
            else:
                messagebox.showerror("Invalid Input", "Number of towers must be between 3 and 15, and disks must be <= towers.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers.")

    num_disks_label = tk.Label(root, text="Number of Disks:")
    num_disks_label.pack()
    num_disks_entry = tk.Entry(root)
    num_disks_entry.pack()

    num_towers_label = tk.Label(root, text="Number of Towers (3-15):")
    num_towers_label.pack()
    num_towers_entry = tk.Entry(root)
    num_towers_entry.pack()

    start_button = tk.Button(root, text="Start Simulation", command=start_simulation)
    start_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()