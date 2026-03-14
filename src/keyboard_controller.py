import argparse
import curses

from drone_rc import DroneRC


class KeyboardController:
    def __init__(self, rc: DroneRC, angle_step: float = 5.0, motor_step: int = 5):
        self.rc = rc
        self.angle_step = angle_step
        self.motor_step = motor_step

        self.motor_percent = 0
        self.pitch_target = 0.0
        self.roll_target = 0.0

    def _clamp(self, value, low, high):
        return max(low, min(value, high))

    def _motor_to_thrust(self) -> int:
        # Firmware expects thrust in [0, 250].
        return int(round(self.motor_percent * 2.5))

    def _apply_commands(self):
        thrust = self._motor_to_thrust()
        self.rc.manual_thrusts(thrust, thrust, thrust, thrust)
        self.rc.set_pitch(self.pitch_target)
        self.rc.set_roll(self.roll_target)

    def _draw(self, stdscr):
        stdscr.erase()
        stdscr.addstr(0, 0, "Drone Keyboard Controller")
        stdscr.addstr(2, 0, f"Motor: {self.motor_percent}%")
        stdscr.addstr(3, 0, f"Pitch target: {self.pitch_target:.1f} deg")
        stdscr.addstr(4, 0, f"Roll target: {self.roll_target:.1f} deg")

        stdscr.addstr(6, 0, "Controls:")
        stdscr.addstr(7, 0, "  +/- : motor percent +/-5")
        stdscr.addstr(8, 0, "  Arrow Up/Down : pitch +/-5 deg")
        stdscr.addstr(9, 0, "  Arrow Left/Right : roll -/+5 deg")
        stdscr.addstr(10, 0, "  Space : zero pitch/roll")
        stdscr.addstr(11, 0, "  0 : motor to 0%")
        stdscr.addstr(12, 0, "  q : emergency stop and quit")
        stdscr.refresh()

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(50)

        self.rc.set_mode(2)
        self._apply_commands()

        while True:
            self._draw(stdscr)
            key = stdscr.getch()
            changed = False

            if key == -1:
                continue

            if key in (ord("q"), ord("Q")):
                break
            if key in (ord("+"), ord("=")):
                self.motor_percent = self._clamp(self.motor_percent + self.motor_step, 0, 100)
                changed = True
            elif key in (ord("-"), ord("_")):
                self.motor_percent = self._clamp(self.motor_percent - self.motor_step, 0, 100)
                changed = True
            elif key == ord("0"):
                self.motor_percent = 0
                changed = True
            elif key == curses.KEY_UP:
                self.pitch_target += self.angle_step
                changed = True
            elif key == curses.KEY_DOWN:
                self.pitch_target -= self.angle_step
                changed = True
            elif key == curses.KEY_LEFT:
                self.roll_target -= self.angle_step
                changed = True
            elif key == curses.KEY_RIGHT:
                self.roll_target += self.angle_step
                changed = True
            elif key == ord(" "):
                self.pitch_target = 0.0
                self.roll_target = 0.0
                changed = True

            if changed:
                self._apply_commands()


def main():

    rc = DroneRC()
    rc.connect()
    rc.msg('rst')
    rc.set_p_gain(20)
    controller = KeyboardController(rc)

    try:
        curses.wrapper(controller.run)
    finally:
        rc.emergency_stop()
        rc.s.close()


if __name__ == "__main__":
    main()