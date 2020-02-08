import time
import os
import json
import terminalio
from adafruit_display_text import label
from displayio import Group

CONSOLE = False
DEBUG = True

MIN_PRESSURE = 8
HIGH_PRESSURE = 40
WAITING = 0
STARTED = 1
DETECTED = 2

SOFT_SIP = 0
HARD_SIP = 1
SOFT_PUFF = 2
HARD_PUFF = 3

COLOR = 0xFFFFFF
FONT = terminalio.FONT

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
Y_OFFSET = 3
TEXT_HEIGHT = 8
BOTTOM_ROW = DISPLAY_HEIGHT - TEXT_HEIGHT
BANNER_STRING = "PUFF-O-TRON-9000"
pressure_string = " "
input_type_string = " "
# duration_str = " "
# pylint:disable=too-many-locals,exec-used,eval-used

STATE_MAP = {
    # STATE
    WAITING: {
        # POLARITY
        0: (
            # STATE STRING
            "WAITING FOR INPUT",
            {
                # PEAK LEVEL
                None:" ",
                # 0: N/A
                # 1: N/A
            }
        ),
        "name":"WAITING"
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

        "name":"STARTED"
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
        "name":"DETECTED"
    },

}

class PuffDetector:
    def __init__(
            self,
            display,
            min_pressure=MIN_PRESSURE,
            high_pressure=HIGH_PRESSURE,
            config_filename="settings.json",
            display_timeout=1,
    ):
        self.display = display
        self.state_display_start = time.monotonic()
        self.detection_result_str = ""
        self.duration_str = ""
        self.high_pressure = high_pressure
        self.min_pressure = min_pressure
        self.current_pressure = 0
        self.start_polarity = 0
        self.peak_level = 0
        self.counter = 0
        self.duration = 0
        self.puff_start = 0
        self.state = WAITING
        self.settings_dict = {}
        self.prev_state = self.state
        self.state_callbacks = []
        self.display_timeout = display_timeout

        self._config_filename = config_filename
        self._load_config()
        if self.settings_dict:
            if "MIN_PRESSURE" in self.settings_dict.keys():
                self.min_pressure = self.settings_dict["MIN_PRESSURE"]
            if "HIGH_PRESSURE" in self.settings_dict.keys():
                self.high_pressure = self.settings_dict["HIGH_PRESSURE"]
            if "DISPLAY_TIMEOUT" in self.settings_dict.keys():
                self.display_timeout = self.settings_dict["DISPLAY_TIMEOUT"]
            if "ACTIONS" in self.settings_dict.keys():
                self.actions = self.settings_dict['ACTIONS']

    def _load_config(self):
        if not self._config_filename in os.listdir("/"):
            return
        try:
            with open(self._config_filename, "r") as file:
                self.settings_dict = json.load(file)
        except (ValueError, OSError) as error:
            print("Error loading config file")
            print(type(error))

    def catagorize_pressure(self, pressure):
        """determine the strength and polarity of the pressure reading"""
        level = 0
        polarity = 0
        abs_pressure = abs(pressure)

        if abs_pressure > self.min_pressure:
            level = 1
        if abs_pressure > self.high_pressure:
            level = 2

        if level != 0:
            if pressure > 0:
                polarity = 1
            else:
                polarity = -1

        return (polarity, level)

    @staticmethod
    def pressure_string(pressure_type):
        polarity, level = pressure_type  # pylint:disable=unused-variable
        pressure_str = "HIGH"
        if level == 0 or polarity == 0:
            return ""
        # print("pressure level:", level)
        if level == 1:
            pressure_str = "LOW"
        elif level == 2:
            pressure_str = "HIGH"

        if polarity == 1:
            pressure_str += "PUFF"
        elif polarity == -1:
            pressure_str += "SIP"
        return pressure_str

    def check_for_puff(self, current_pressure):
        """Updates the internal state to detect if a sip/puff has been started or stopped"""

        self.current_pressure = current_pressure
        puff_peak_level = None
        puff_duration = None
        polarity, level = self.catagorize_pressure(current_pressure)

        if self.state == DETECTED:
            # if polarity == 0 and level == 0:
            self.state = WAITING

            self.start_polarity = 0
            self.peak_level = 0
            self.duration = 0
        if level != 0 and self.start_polarity == 0:
            self.state = STARTED
            self.start_polarity = polarity
            self.puff_start = time.monotonic()

        if self.state == STARTED:
            # if self.start_polarity != 0:
            if level > self.peak_level:
                self.peak_level = level

        # if (level == 0) and (self.start_polarity != 0):
        if (level == 0) and (self.state == STARTED):
            self.state = DETECTED
            self.duration = time.monotonic() - self.puff_start

            puff_peak_level = self.peak_level
            puff_duration = self.duration

        self.counter += 1
        puff_status =  (self.start_polarity, puff_peak_level, puff_duration)
        self.process_actions(puff_status)

        return puff_status

    def process_actions(self, puff_stat):
        state_changed = self.prev_state == self.state
        self.prev_state = self.state
        if state_changed:
            return

        for action, action_class in self.actions:
            exec("import %s"%action)

            safe_locals = {
                "self": self,
                "puff_stat":puff_stat,
                "state_map" : STATE_MAP,
                action : eval(action),
            }
            exec("%s.%s.run(self, state_map, puff_stat)"%(action, action_class), {} , safe_locals)





    def log_state_change(self, puff_stat):
        state_changed = self.prev_state == self.state
        self.prev_state = self.state
        if state_changed:
            return
        polarity, peak_level, duration  = puff_stat

        state_str = STATE_MAP[self.state][polarity][0]
        input_type_str = STATE_MAP[self.state][polarity][1][peak_level]
        state_str = state_str.replace(" ", "_").upper()
        if self.state is WAITING:
            print(state_str)
        if self.state is STARTED:
            print(state_str.replace(" ", "_").upper())
        if self.state is DETECTED:
            type_detected = input_type_str[0]
            log_str = "%s::%s::DURATION:%0.3f"%(state_str, type_detected, duration)
            print(log_str)

    def update_display(self, press_str, puff_stat):
        curr_time = time.monotonic()
        polarity, peak_level, duration  = puff_stat

        state_str = STATE_MAP[self.state][polarity][0]
        input_type_str = STATE_MAP[self.state][polarity][1][peak_level]


        if self.state == DETECTED:
            self.duration_str = "Duration: %0.2f" % duration

            self.detection_result_str = input_type_str[0]
            self.state_display_start = curr_time

        elif self.state == WAITING:
            display_elapsed = (curr_time - self.state_display_start)
            if display_elapsed > self.display_timeout:
                self.detection_result_str = " "
                self.duration_str = " "

        min_press_str = "min: %d" % self.min_pressure
        high_press_str = "hi: %d" % self.high_pressure
        banner = label.Label(FONT, text=BANNER_STRING, color=COLOR)
        state = label.Label(FONT, text=state_str, color=COLOR)
        detector_result = label.Label(FONT, text= self.detection_result_str, color=COLOR)
        duration = label.Label(FONT, text=self.duration_str, color=COLOR)
        min_pressure_label = label.Label(FONT, text=min_press_str, color=COLOR)
        high_pressure_label = label.Label(FONT, text=high_press_str, color=COLOR)
        pressure_label = label.Label(FONT, text=press_str, color=COLOR)

        banner.x = 0
        banner.y = 0 + Y_OFFSET

        state.x = 10
        state.y = 10 + Y_OFFSET

        detector_result.x = 10
        detector_result.y = 20 + Y_OFFSET

        duration.x = 10
        duration.y = 30 + Y_OFFSET

        min_pressure_label.x = 0
        min_pressure_label.y = BOTTOM_ROW - 10

        pressure_label.x = DISPLAY_WIDTH - pressure_label.bounding_box[2]
        pressure_label.y = BOTTOM_ROW

        high_pressure_label.x = 0
        high_pressure_label.y = BOTTOM_ROW

        splash = Group(max_size=10)
        splash.append(banner)
        splash.append(state)
        splash.append(detector_result)
        splash.append(duration)
        splash.append(min_pressure_label)
        splash.append(high_pressure_label)
        splash.append(pressure_label)

        self.display.show(splash)
