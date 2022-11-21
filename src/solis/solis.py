import pysolarmanv5

ENERGY_CONTROL_REG = 43110


class Solis:
    def __init__(self, ip: str, serial: int, port: int = 8899):
        self._modbus = pysolarmanv5.PySolarmanV5(ip, serial, port=port)

    def charge(self, enable: bool):
        """
        Sets the inverter to charge from the grid
        """
        # Online references show the bit masks to be as follows:
        # 00 - Spontaneous mode switch (see user manual) 0—Off 1—On
        # 01 - Optimized revenue mode switch (see user manual, timed charge/discharge)
        #      0—Off 1—On
        # 02 - Energy storage off-grid mode switch (see user manual) 0—Off 1—On
        # 03 - Battery wake-up switch (1 -wake-up enable 0 - wake-up is not enabled,
        #      see user manual) 0—Off 1—On
        # 04 - Reserved 0—Off 1—On
        # 05 - Reserved 0—Off 1—On
        # 06 - Reserved 0—Off 1—On
        # 07 - Reserved 0—Off 1—On
        # 08 - Reserved 0—Off 1—On
        # 09 - Reserved 0—Off 1—On
        # 10 - Reserved 0—Off 1—On
        # 11 - Reserved 0—Off 1—On
        # 12 - Reserved 0—Off 1—On
        # 13 - Reserved 0—Off 1—On
        # 14 - Reserved 0—Off 1—On
        # 15 - Reserved 0—No 1—Yes

        # Observations show:
        # Self-Use mode: 000001
        # Draw normal load from grid instead of batt: 000010
        # Allowing charge from grid: 100000

        value: int = 0b00000001
        if enable:
            print("Enabling charging from grid")
            value = value | 0b100010
        else:
            print("Disabling charging from grid")
        self._modbus.write_holding_register(ENERGY_CONTROL_REG, value=value)

    def stats(self):
        discharing = self._modbus.read_input_register_formatted(33135, quantity=1)
        batt = self._modbus.read_input_register_formatted(
            33149, quantity=2, signed=True
        )
        if discharing:
            print(f"Battery discharging: {batt} W")
        else:
            print(f"Battery charging: {batt} W")

        batt_charge_level = self._modbus.read_input_register_formatted(
            33139, quantity=1
        )
        print(f"Battery Level: {batt_charge_level}%")

        control_reg = self._modbus.read_holding_register_formatted(
            ENERGY_CONTROL_REG, quantity=1
        )
        print(control_reg)
