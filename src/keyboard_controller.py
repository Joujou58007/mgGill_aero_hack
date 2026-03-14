import curses
from drone_manager import DroneManager

class KeyboardController:
    def __init__(self, drone_manager: DroneManager):
        self.drone_manager = drone_manager
        self.angle_step = 5.0
        self.motor_step = 5
        self.pitch_target = 0.0
        self.roll_target = 0.0

    def _clamp(self, value, low, high):
        return max(low, min(value, high))

    def _motor_to_thrust(self) -> int:
        return int(round(self.motor_percent * 2.5))

    def _apply_commands(self, motor_increment):
        if motor_increment and motor_increment != 0:
            self.drone_manager.increment_thrusts(motor_increment)
        self.drone_manager.set_pitch(self.pitch_target)
        self.drone_manager.set_roll(self.roll_target)

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
        self._apply_commands()

        while True:
            self._draw(stdscr)
            key = stdscr.getch()
            changed = False
            motor_increment = 0

            if key == -1:
                continue
            if key in (ord("q"), ord("Q")):
                break
            if key in (ord("+"), ord("=")):
                motor_increment += self.motor_step
                changed = True
            elif key in (ord("-"), ord("_")):
                motor_increment -= self.motor_step
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
                self._apply_commands(motor_increment)
