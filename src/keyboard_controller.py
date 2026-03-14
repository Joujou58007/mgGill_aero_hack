import curses
from drone_manager import DroneManager

class KeyboardController:
    def __init__(self, drone_manager: DroneManager):
        self.drone_manager = drone_manager
        self.angle_step = 1.0
        self.motor_step = 1
        self.motor_target = 0
        self.pitch_target = 0.0
        self.roll_target = 0.0

    def _draw(self, stdscr):
        stdscr.erase()

        stdscr.addstr(1, 0, f"Motor target: {self.motor_target}")
        stdscr.addstr(2, 0, f"Pitch target: {self.pitch_target:.1f}")
        stdscr.addstr(3, 0, f"Roll target: {self.roll_target:.1f}")

        stdscr.addstr(5, 0, "W/S : motor percent +/-")
        stdscr.addstr(6, 0, "Arrow Up/Down : pitch +/-")
        stdscr.addstr(7, 0, "Arrow Left/Right : roll +/-")
        stdscr.addstr(8, 0, "Space : zero pitch/roll")
        stdscr.addstr(9, 0, "q : emergency stop and quit")
        stdscr.refresh()

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(50)

        while True:
            self._draw(stdscr)
            key = stdscr.getch()

            if key == -1:
                continue
            if key in (ord("q"), ord("Q")):
                self.drone_manager.disable_motors()
                return
            if key in (ord("w"), ord("W")):
                self.motor_target += self.motor_step
                self.drone_manager.increment_thrusts(self.motor_step)
            elif key in (ord("s"), ord("S")):
                self.motor_target -= self.motor_step
                self.drone_manager.increment_thrusts(-self.motor_step)
            elif key == curses.KEY_UP:
                self.pitch_target += self.angle_step
                self.drone_manager.set_pitch(self.pitch_target)
            elif key == curses.KEY_DOWN:
                self.pitch_target -= self.angle_step
                self.drone_manager.set_pitch(self.pitch_target)
            elif key == curses.KEY_LEFT:
                self.roll_target -= self.angle_step
                self.drone_manager.set_roll(self.roll_target)
            elif key == curses.KEY_RIGHT:
                self.roll_target += self.angle_step
                self.drone_manager.set_roll(self.roll_target)
            elif key == ord(" "):
                self.pitch_target = 0.0
                self.roll_target = 0.0
                self.drone_manager.set_pitch(self.pitch_target)
                self.drone_manager.set_roll(self.roll_target)