from drone_manager import DroneManager
import time

def main():
    drone_manager = DroneManager(16, is_flight_mode=False, p=0.02, i=0.00001, d=5)
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
