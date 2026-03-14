from drone_rc import DroneRC
import time

def main():
    print("Hello from main")
    drone_rc = DroneRC()
    drone_rc.connect()
    while True:
        print("Hello from loop")
        time.sleep(1)
        pitch = drone_rc.get_pitch()
        print(pitch)

if __name__ == "__main__":
    main()
