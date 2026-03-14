import curses
import time
from drone_manager import DroneManager
from keyboard_controller import KeyboardController

def main():
    drone_manager = DroneManager(16, is_flight_mode=False, p=0.02, i=0.00001, d=5)
    drone_manager.execute(logic)

def logic(drone_manager: DroneManager):
    time.sleep(1)
    print("Starting logic")

    keyboard_controller = KeyboardController(drone_manager)
    curses.wrapper(keyboard_controller.run)

if __name__ == "__main__":
    main()
