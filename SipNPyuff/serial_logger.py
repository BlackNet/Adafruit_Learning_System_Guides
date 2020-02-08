class SerialLogger:
    @classmethod
    def run(cls, detector, state_map, puff_stat):
        polarity, peak_level, duration  = puff_stat
        state_str = state_map[detector.state][polarity][0]
        state_str = state_str.replace(" ", "_").upper()

        input_type_str = state_map[detector.state][polarity][1][peak_level]

        if state_map[detector.state]['name'] == 'WAITING':
            print(state_str)


        if state_map[detector.state]['name']  == 'STARTED':
            print(state_str.replace(" ", "_").upper())

        if state_map[detector.state]['name']  == 'DETECTED':
            type_detected = input_type_str[0].replace(" ", "_").upper()
            log_str = "%s::%s::DURATION:%0.3f"%(state_str, type_detected, duration)
            print(log_str)
