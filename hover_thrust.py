import socket
from time import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.4.16", 8080))

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

thrust = 0

if __name__ == "__main__":
    set_mode(2)

    while True:
        increment_thrusts(thrust, thrust, thrust, thrust)
        x = input("Press enter to increase thrust by 10, or Ctrl-C to quit.")
        if x == "a":
            thrust += 10
        elif x == "z":
            thrust -= 5
        elif x == "x":
            e()
        print("Thrust:", thrust)





