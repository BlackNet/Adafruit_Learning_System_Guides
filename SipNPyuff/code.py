import time
import board
import displayio
import terminalio
from adafruit_display_text import label
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

# pylint:disable=unused-variable,too-many-locals,unused-argument


def update_display(duration_str, press_str, puff_detector, state_map, puff_stat):
    polarity, peak_level, duration  = puff_stat

    state_str = state_map[puff_detector.state][polarity][0]
    input_type_str = state_map[puff_detector.state][polarity][1][peak_level]

    min_press_str = "min: %d" % puff_detector.min_pressure
    high_press_str = "hi: %d" % puff_detector.high_pressure

    banner = label.Label(font, text=banner_string, color=color)
    state = label.Label(font, text=state_str, color=color)
    detector_result = label.Label(font, text= input_type_string, color=color)
    duration = label.Label(font, text=duration_str, color=color)
    min_pressure_label = label.Label(font, text=min_press_str, color=color)
    high_pressure_label = label.Label(font, text=high_press_str, color=color)
    pressure_label = label.Label(font, text=press_str, color=color)

    banner.x = 0
    banner.y = 0 + Y_OFFSET

    state.x = 20
    state.y = 10 + Y_OFFSET
    detector_result.x = 20
    detector_result.y = 20 + Y_OFFSET

    duration.x = 10
    duration.y = 30 + Y_OFFSET

    min_pressure_label.x = 0
    min_pressure_label.y = BOTTOM_ROW - 10

    x, y, w, h = pressure_label.bounding_box
    pressure_label.x = DISPLAY_WIDTH - w
    pressure_label.y = BOTTOM_ROW

    high_pressure_label.x = 0
    high_pressure_label.y = BOTTOM_ROW

    splash = displayio.Group(max_size=10)
    splash.append(banner)
    splash.append(state)
    splash.append(detector_result)
    splash.append(duration)
    splash.append(min_pressure_label)
    splash.append(high_pressure_label)
    splash.append(pressure_label)

    display.show(splash)


displayio.release_displays()

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
Y_OFFSET = 3
TEXT_HEIGHT = 8
BOTTOM_ROW = DISPLAY_HEIGHT - TEXT_HEIGHT

SOFT_SIP = 0
HARD_SIP = 1
SOFT_PUFF = 2
HARD_PUFF = 3
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
detector = PuffDetector()
time.sleep(1)
color = 0xFFFFFF
font = terminalio.FONT

banner_string = "PUFF-O-TRON-9000"
state_string = "  "
pressure_string = " "
input_type_string = " "
duration_string = " "

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
            "Detected",
            (
                None,
                ("SOFT PUFF", SOFT_PUFF),
                ("HARD PUFF", HARD_PUFF)
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
    if detector.state == DETECTED:
        duration_string = "Duration: %0.2f" % puff_duration

        state_display_start = curr_time

    elif detector.state == WAITING:
        if (curr_time - state_display_start) > detector.display_timeout:
            input_type_string = " "
            duration_string = " "

    update_display(duration_string, pressure_string, detector, state_mapper, puff_status)
    detector.log_state_change(state_mapper, puff_status)
