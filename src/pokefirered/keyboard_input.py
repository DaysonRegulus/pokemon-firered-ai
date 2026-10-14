"""
Cross-platform non-blocking keyboard input module.
Supports both Windows (msvcrt) and Unix/Linux (termios/tty/select).
"""
import sys

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import msvcrt

    class KeyboardInput:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def get_key(self):
            """
            Non-blocking keyboard read on Windows.
            Returns the pressed character in lowercase, or None if no key pressed.
            """
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                # Handle special keys (arrows, function keys) which send a prefix byte
                if ch in (b'\x00', b'\xe0'):
                    msvcrt.getch()  # flush second byte
                    return None
                try:
                    return ch.decode('utf-8', errors='ignore').lower()
                except Exception:
                    return None
            return None

else:
    import termios
    import tty
    import select

    class KeyboardInput:
        def __enter__(self):
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

        def get_key(self):
            """
            Non-blocking keyboard read on POSIX systems.
            """
            dr, _, _ = select.select([sys.stdin], [], [], 0)
            if dr:
                try:
                    return sys.stdin.read(1).lower()
                except Exception:
                    return None
            return None


def key_to_action(key):
    """
    Convert keyboard key to 6-action array for ActionFilterWrapper:
    0: B (key 'z')
    1: UP (key 'w')
    2: DOWN (key 's')
    3: LEFT (key 'a')
    4: RIGHT (key 'd')
    5: A (key 'x')
    """
    import numpy as np

    action = np.zeros(6, dtype=np.int8)
    if key == "z":
        action[0] = 1  # B
    elif key == "w":
        action[1] = 1  # UP
    elif key == "s":
        action[2] = 1  # DOWN
    elif key == "a":
        action[3] = 1  # LEFT
    elif key == "d":
        action[4] = 1  # RIGHT
    elif key == "x":
        action[5] = 1  # A
    return action
