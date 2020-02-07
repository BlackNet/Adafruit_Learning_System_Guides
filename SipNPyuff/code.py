import time
import board
import displayio
import adafruit_displayio_ssd1306
import adafruit_lps35hw
from puff_detector import PuffDetector, STARTED, DETECTED, WAITING

# from adafruit_hid.keyboard import Keyboard
# from adafruit_hid.keycode import Keycode

# # The keycode sent for each button, will be paired with a control key
# buttonkeys = [Keycode.A, Keycode.B, Keycode.C, Keycode.D, Keycode.E, Keycode.F]
# controlkey = Keycode.LEFT_CONTROL

# # the keyboard object!
# kbd = Keyboard()

displayio.release_displays()

SOFT_SIP = 0
HARD_SIP = 1
SOFT_PUFF = 2
HARD_PUFF = 3

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
i2c = board.I2C()

display_bus = displayio.I2CDisplay(i2c, device_address=0x3D)
display = adafruit_displayio_ssd1306.SSD1306(
    display_bus, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT
)

lps = adafruit_lps35hw.LPS35HW(i2c, 0x5C)
lps.zero_pressure()
lps.data_rate = adafruit_lps35hw.DataRate.RATE_75_HZ

lps.filter_enabled = True
lps.filter_config = True
detector = PuffDetector(display)
time.sleep(1)

print("minimum pressure:", detector.min_pressure)
print("high pressure threshold:", detector.high_pressure)

state_mapper = {
    # STATE
    WAITING: {
        # POLARITY
        0: (
            # STATE STRING
            "Waiting for Input",
            {
                # PEAK LEVEL
                None:" ",
                # 0: N/A
                # 1: N/A
            }
        ),
    },

    # STATE
    STARTED: {
        # POLARITY
        1: (
            # STATE STRING
            "PUFF STARTED",
            {
                # PEAK LEVEL
                None:" ",
                # 0: N/A
                # 1: N/A
            },
        ),
        -1: (
            # STATE STRING
            "SIP STARTED",
            {
                # PEAK LEVEL
                None:" ",
                # 0: N/A
                # 1: N/A
            },
        ),
    }, # state: 2,  pol: 1, 1, peak: 2

    # STATE
    DETECTED: {
        # POLARITY
        1: (
            # STATE STRING
            " ",
            (
                None,
                ("SOFT PUFF DETECTED", SOFT_PUFF),
                ("HARD PUFF DETECTED", HARD_PUFF)
            )
        ),
        -1: (
            # STATE STRING
            "Detected",
            (
                None,
                ("SOFT SIP", SOFT_SIP),
                ("HARD SIP", HARD_SIP)
            )
        ),
    },
}

state_display_timeout = 1.0
state_display_start = 0
while True:
    detected_puff = None
    curr_time = time.monotonic()

    current_pressure = lps.pressure
    pressure_string = "Press: %0.3f" % current_pressure

    puff_status = detector.check_for_puff(current_pressure)
    puff_polarity, puff_peak_level, puff_duration = puff_status


    detector.update_display(pressure_string, state_mapper, puff_status)
    detector.log_state_change(state_mapper, puff_status)
