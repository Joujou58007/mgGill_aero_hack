import socket
import subprocess
import select
import time

class DroneManager:
    def __init__(self, number, p, i, d, is_flight_mode=False):
        self.socket = None
        self.number = number
        self.p = p
        self.i = i
        self.d = d
        self.is_flight_mode = is_flight_mode
    
    def execute(self, callback):
        try:
            self.safe_execute(callback)
        finally:
            self.connect_wifi("eduroam")
    
    def safe_execute(self, callback):
        result = self.connect_wifi(f"AeroHacks Drone {self.number}", "skibidi123")
        if not result:
            print(f"Failed to connect to drone {self.number}")
            return
        self.connect_socket("192.168.4.1", 8080)
        print(f"Successfully connected to drone {self.number}")
        self.set_pid_config()
        self.recalibrate()
        self.turn_on_blue()
        self.turn_on_green()
        self.reset_pid()
        if self.is_flight_mode:
            self.enable_motors()
        print("Initialization done")
        try:
            callback(self)
        finally:
            self.disable_motors()

    def connect_wifi(self, ssid, password=None):
        cmd = ["nmcli", "device", "wifi", "connect", ssid]
        if password:
            cmd += ["password", password]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True
        else:
            return False
    
    def connect_socket(self, ip, port):
        if self.socket:
            self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
    
    def turn_on_blue(self):
        self.send_msg("lb1")
    
    def turn_on_green(self):
        self.send_msg("lg1")
    
    def send_command(self, command):
        self.flush_socket()
        self.socket.sendall((command + "\n").encode("ASCII"))
        rx = ""
        while not rx.endswith("\n"):
            rx += self.socket.recv(1).decode("ASCII")
        return rx[:-1]

    def send_msg(self, msg):
        self.flush_socket()
        self.socket.sendall((msg + "\n").encode("ASCII"))
    
    def flush_socket(self):
        input_ready, _, _ = select.select([self.socket], [], [], 0.0)
        while input_ready:
            data = self.socket.recv(1)
            if not data:
                break
            input_ready, _, _ = select.select([self.socket], [], [], 0.0)
    
    def lock_motors(self):
        print("Locking motors")
        self.send_msg("lck")

    def enable_motors(self):
        print("Enabling motors")
        self.send_msg("mode2")
    
    def disable_motors(self):
        print("Disabling motors")
        self.send_msg("mode0")
    
    def set_pid_config(self):
        self.send_msg("gainP" + str(self.p))
        self.send_msg("gainI" + str(self.i))
        self.send_msg("gainD" + str(self.d))

    def recalibrate(self):
        print("Recalibrating...")
        self.send_command("rst")
    
    def reset_pid(self):
        self.send_msg("irst")

    def get_pitch(self):
        return float(self.send_command("angX"))

    def increment_thrusts(self, value):
        self.send_msg("incT\n" + str(value) + "," + str(value) + "," + str(value) + "," + str(value) + "\n")

    def set_pitch(self, r):
        self.send_msg("gx" + str(r))

    def set_roll(self, r):
        self.send_msg("gy" + str(r))
