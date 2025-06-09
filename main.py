import customtkinter as ctk
from gui import AppGUI
from data_loader import DataLoader
from scheduler import Scheduler
from route_optimizer import RouteOptimizer

def main():
    # Initialize components
    loader = DataLoader()
    scheduler = Scheduler(loader)
    route_opt = RouteOptimizer(loader)
    
    # Create and run GUI
    app = AppGUI(scheduler, route_opt, loader)
    app.mainloop()

if __name__ == "__main__":
    main()

