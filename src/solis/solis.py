import pysolarmanv5
from . import exceptions
import struct

REG_ENERGY_CONTROL = 43110
REG_CHARGING = 33135

REG_INFO_START = 33000
REG_INFO_END = 33286


class SolisInfoRegs:
    def __init__(self, modbus):
        self.modbus = modbus
        self.reg_start = 33000
        self.reg_end = 33286
        self.regs = [None] * self.reg_len

    @property
    def reg_len(self):
        return self.reg_end - self.reg_start

    def update(self):
        self.regs = self.modbus.read_input_registers(self.reg_start, 100)
        self.regs += self.modbus.read_input_registers(self.reg_start + 100, 100)
        self.regs += self.modbus.read_input_registers(
            self.reg_start + 200, self.reg_len - 200
        )

    def get(self, addr, count):
        addr -= self.reg_start
        return self.regs[addr : addr + count]

    def get_s32(self, addr):
        regs = self.get(addr, 2)
        b = regs[0].to_bytes(2, "big") + regs[1].to_bytes(2, "big")
        result = int.from_bytes(b, "big", signed=True)
        return result

    def get_u16(self, addr):
        return self.get(addr, 1)[0]

    def get_ascii(self, addr, count):
        # 160F52217230151
        regs = self.get(addr, count)
        data = []
        for reg in regs:
            val1 = reg & 0b11111111
            val2 = reg >> 8
            data.append(chr(val2))
            data.append(chr(val1))

        return "".join(data)


class Solis:
    def __init__(self, ip: str, serial: int, port: int = 8899):
        self._serial = serial
        try:
            self._modbus = pysolarmanv5.PySolarmanV5(ip, serial, port=port)
        except struct.error:
            raise exceptions.SerialInvalid("Invalid serial number provided")
        except pysolarmanv5.pysolarmanv5.NoSocketAvailableError:
            raise exceptions.ConnectionError("Cannot Connect")

        self.info_regs = SolisInfoRegs(self._modbus)

    def update(self):
        self.info_regs.update()

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
        self._modbus.write_holding_register(REG_ENERGY_CONTROL, value=value)

    @property
    def charging(self):
        """
        Returns the charging state of the batteries
          True: Battery is charing
          False: Battery is discharing
        """
        discharging: bool = self.info_regs.get(33135, 1)[0]
        return not discharging

    @property
    def batt_charge_rate(self):
        batt = self.info_regs.get_s32(33149)
        if not self.charging:
            batt = -batt
        return batt

    @property
    def batt_charge_level(self):
        return self.info_regs.get_u16(33139)

    @property
    def serial(self):
        # 160F52217230151
        return self.info_regs.get_ascii(33004, 15)

    @property
    def sw_dsp_version(self):
        return self.info_regs.get_u16(33001)
