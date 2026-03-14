import socket

class DroneRC:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self):
        print("Connecting to socket")
        self.s.connect(("192.168.4.1", 8080))
        print("Connected to socket")

    def msg(self, tx):
        self.s.sendall((tx + "\n").encode("ASCII"))
        rx = ""
        while not rx.endswith("\n"):
            rx += self.s.recv(1).decode("ASCII")
        return rx[:-1]

    def emergency_stop(self):
        self.msg("mode0")

    def e(self):
        self.emergency_stop()

    # mode 0: off
    # mode 1: full manual motor control
    # mode 2: PID control for pitch and roll
    def set_mode(self, m):
        self.msg("mode" + str(m))

    def get_mode(self):
        return self.msg("gMode")

    # always between 0 and 250
    # in mode 2 sets baseline value in PID results are added to
    def manual_thrusts(self, A, B, C, D):
        self.msg("manT\n" + str(A) + "," + str(B) + "," + str(C) + "," + str(D) + "\n")

    # same as prev function, but increments last value instead of overwriting
    def increment_thrusts(self, A, B, C, D):
        self.msg("incT\n" + str(A) + "," + str(B) + "," + str(C) + "," + str(D) + "\n")

    def get_pitch(self): # unit close-ish to degrees, but not exact
        return float(self.msg("angX")) / 16

    def get_roll(self): # unit close-ish to degrees, but not exact
        return float(self.msg("angY")) / 16

    def get_gyro_pitch(self): # pitch rate in degree/sec
        return float(self.msg("gyroX"))

    def get_gyro_roll(self): # roll rate in degree/sec
        return float(self.msg("gyroY"))

    # target pitch to aim for in mode 2
    # same unit as get_pitch()
    def set_pitch(self, r):
        self.msg("gx" + str(r))

    # target roll to aim for in mode 2
    # same unit as get_roll()
    def set_roll(self, r):
        self.msg("gy" + str(r))

    def set_p_gain(self, p): # approx 0 - 0.5
        self.msg("gainP" + str(p))

    def set_i_gain(self, i): # below 0.00003
        self.msg("gainI" + str(i))

    def set_d_gain(self, d): # approx 0 - 10
        self.msg("gainD" + str(d))

    def red_LED(self, val): # controls LED light. 1 for on, 0 for off
        self.msg("lr" + str(val))

    def blue_LED(self, val):
        self.msg("lb" + str(val))

    def green_LED(self, val):
        self.msg("lg" + str(val))

    def reset_integral(self): # resets the value of integrands in the PID loops to 0
        self.msg("irst")

    # returns [I_x, I_y] the integrands from the pitch and roll pid loops
    def get_i_values(self):
        resp = self.msg("geti").split(",")
        return [float(resp[0]), float(resp[1])]

    def set_yaw(self, y): # directly sets motor difference for yaw control
        self.msg("yaw" + str(y))
