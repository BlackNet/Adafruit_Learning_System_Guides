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

 # pylint:disable=unused-variable,too-many-locals

def display_info(input_type_str, duration_str, press_str, puff_detector):
    state_str = state_mapper[puff_detector.state][0]

    min_press_str = "min: %d" % puff_detector.min_pressure
    high_press_str = "hi: %d" % puff_detector.high_pressure

    banner = label.Label(font, text=banner_string, color=color)
    state = label.Label(font, text=state_str, color=color)
    detector_result = label.Label(font, text=input_type_str, color=color)
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

# maps a combination of polarity and peak_level to an input_type
input_mapper = {
    1: (None, ("SOFT PUFF", SOFT_PUFF), ("HARD PUFF", HARD_PUFF)),
    -1: (None, ("SOFT SIP", SOFT_SIP), ("HARD SIP", HARD_SIP)),
}

state_mapper = {
    WAITING: ("Waiting for Input",),
    STARTED: ("Input started",),
    DETECTED: ("Detected",),
}

state_display_timeout = 1.0
state_display_start = 0
while True:
    detected_puff = None
    curr_time = time.monotonic()
    # Set text, font, and color

    current_pressure = lps.pressure
    pressure_string = "Press: %0.3f" % current_pressure

    puff_polarity, puff_peak_level, puff_duration = detector.check_for_puff(
        current_pressure
    )
    if detector.state == DETECTED:
        duration_string = "Duration: %0.2f" % puff_duration

        input_type_string, input_type = input_mapper[puff_polarity][puff_peak_level]
        state_display_start = curr_time

    elif detector.state == STARTED:
        dir_string = ""
        if puff_polarity == 1:
            dir_string = "PUFF"
        if puff_polarity == -1:
            dir_string = "SIP"

    elif detector.state == WAITING:
        if (curr_time - state_display_start) > detector.display_timeout:
            input_type_string = " "
            duration_string = " "

    ########### process displaying info ###################

    display_info(input_type_string, duration_string, pressure_string, detector)
