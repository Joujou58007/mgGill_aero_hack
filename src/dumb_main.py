import socket
from time import monotonic, sleep
from PID import PIDController

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.4.1", 8080))

def msg(tx, fake=False):
    if fake:
        print("TX:", tx)
        return "0"
    else:
        s.sendall((tx + "\n").encode("ASCII"))
        rx = ""
        while not rx.endswith("\n"):
            rx += s.recv(1).decode("ASCII")
        return rx[:-1]


def emergency_stop():
    msg("mode0")

def e():
    emergency_stop()

# mode 0: off
# mode 1: full manual motor control
# mode 2: PID control for pitch and roll
def set_mode(m):
    msg("mode" + str(m))

def get_mode():
    return msg("gMode")

# same as prev function, but increments last value instead of overwriting
def increment_thrusts(A, B, C, D):
    msg("manT\n" + str(A) + "," + str(B) + "," + str(C) + "," + str(D) + "\n")

def set_pitch(r):
    msg("gx" + str(r))

# target roll to aim for in mode 2
# same unit as get_roll()
def set_roll(r):
    msg("gy" + str(r))

class Flight:
    def __init__(self):
        self.base_thrust = 0
        self.roll_pid = PIDController(kp=0.1, ki=0.01, kd=0.05, max_output=20, max_i=100, deriv_tau=0.1)
        self.pitch_pid = PIDController(kp=0.1, ki=0.01, kd=0.05, max_output=20, max_i=100, deriv_tau=0.1)
        self.alt_pid = PIDController(kp=0.1, ki=0.01, kd=0.05, max_output=20, max_i=100, deriv_tau=0.1)

        set_mode(2)

        self.roll_axis_error = 0
        self.pitch_axis_error = 0
        self.alt_error = 0

        hz = 30
        self.dt = 1/hz
        self._next_pid_tick = monotonic() + self.dt

        self.roll_output = 0.0
        self.pitch_output = 0.0
        self.alt_output = 0.0



    def get_error_roll(self):
        return self.roll_axis_error, self.alt_error
        #Julien met ton shit ici
        #alt ici genre

    
    def get_error_pitch(self):
        #Met ton autre shit ici
        return self.pitch_axis_error, self.alt_error
    
    def step_pids(self):
        now = monotonic()

        if now < self._next_pid_tick:
            sleep(self._next_pid_tick - now)
            now = monotonic()
        elif now - self._next_pid_tick > self.dt:
            # If loop work overruns, resync to avoid accumulated drift.
            self._next_pid_tick = now

        self._next_pid_tick += self.dt

        self.roll_output = self.roll_pid.compute(self.roll_axis_error, self.dt)
        self.pitch_output = self.pitch_pid.compute(self.pitch_axis_error, self.dt)
        self.alt_output = self.alt_pid.compute(self.alt_error, self.dt)


    def loop(self):
        while True:
            self.get_error_pitch()
            self.get_error_roll()
            self.step_pids()
            self.send_commands()

    def send_commands(self):
        return None




