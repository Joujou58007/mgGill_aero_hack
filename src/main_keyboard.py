import curses
import time
from drone_manager import DroneManager
from keyboard_controller import KeyboardController

def main():
    drone_manager = DroneManager(8, 35, 0.1, 0.1, is_flight_mode=False)
    drone_manager.execute(logic)

def logic(drone_manager: DroneManager):
    time.sleep(1)
    print("Starting logic")

    keyboard_controller = KeyboardController(drone_manager)
    curses.wrapper(keyboard_controller.run)

if __name__ == "__main__":
    main()
