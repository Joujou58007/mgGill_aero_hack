from drone_manager import DroneManager
import time

def main():
    drone_manager = DroneManager(8, 35, 0.1, 0.1, is_flight_mode=False)
    drone_manager.execute(logic)

def logic(drone_manager: DroneManager):
    time.sleep(5)
    print("Starting loop")

    while True:
        pitch = drone_manager.get_pitch()
        print(pitch)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
