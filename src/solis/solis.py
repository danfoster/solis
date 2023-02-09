import pysolarmanv5
from . import exceptions
import struct

ENERGY_CONTROL_REG = 43110


class Solis:
    def __init__(self, ip: str, serial: int, port: int = 8899):
        try:
            self._modbus = pysolarmanv5.PySolarmanV5(ip, serial, port=port)
        except struct.error:
            raise exceptions.SerialInvalid("Invalid serial number provided")

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

    @property
    def charging(self):
        """
        Returns the charging state of the batteries
          True: Battery is charing
          False: Battery is discharing
        """
        discharging: bool = self._modbus.read_input_register_formatted(
            33135, quantity=1
        )
        return not discharging

    @property
    def batt_charge_rate(self):
        batt = self._modbus.read_input_register_formatted(
            33149, quantity=2, signed=True
        )
        if not self.charging:
            batt = -batt
        return batt

    @property
    def batt_charge_level(self):
        batt_charge_level = self._modbus.read_input_register_formatted(
            33139, quantity=1
        )
        return batt_charge_level

    @property
    def invertor_total_power_generation(self):
        batt = self._modbus.read_input_register_formatted(
            33149, quantity=2, signed=True
        )
        if not self.charging:
            batt = -batt
        return batt

    @property
    def serial(self):
        # 160F52217230151
        regs = self._modbus.read_input_registers(33004, 15)
        data = []
        for reg in regs:
            val1 = reg & 0b11111111
            val2 = reg >> 8
            data.append(chr(val2))
            data.append(chr(val1))

        return "".join(data)
