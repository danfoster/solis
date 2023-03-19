import pysolarmanv5
from . import exceptions
import struct
import logging
import traceback
from time import sleep
import asyncio

REG_ENERGY_CONTROL = 43110
REG_CHARGING = 33135

REG_INFO_START = 33000
REG_INFO_END = 33286

logger = logging.getLogger(__name__)

class SolisInfoRegs:
    def __init__(self, modbus):
        self.modbus = modbus
        self.reg_start = 33000
        self.reg_end = 33286
        self.regs = [None] * self.reg_len

    @property
    def reg_len(self):
        return self.reg_end - self.reg_start

    async def get_regs(self):
        regs = await self.modbus.read_input_registers(self.reg_start, 100)
        regs += await self.modbus.read_input_registers(self.reg_start + 100, 100)
        regs += await self.modbus.read_input_registers(
            self.reg_start + 200, self.reg_len - 200
        )
        return regs

    async def async_update(self):
        COUNT = 10
        logger.debug("Starting Update")
        for i in range(1, COUNT+1):
            await asyncio.sleep(i-1)
            try:
                self.regs = await self.get_regs()
                logger.debug("Finishing Update")
                return
            except pysolarmanv5.pysolarmanv5_async.V5FrameError as err:
                logger.info("[%s/%s] Error Updating: %s", i, COUNT, err)
                logger.debug(traceback.format_exc())
                continue
            except struct.error as err:
                logger.info("[%s/%s] Error Updating: %s", i, COUNT, err)
                logger.debug(traceback.format_exc())
                continue
            except ConnectionResetError as err:
                logger.info("[%s/%s] Error Updating: %s", i, COUNT, err)
                logger.debug(traceback.format_exc())
                continue
            except TimeoutError as err:
                logger.info("[%s/%s] Error Updating: %s", i, COUNT, err)
                logger.debug(traceback.format_exc())
                continue


        raise exceptions.UpdateError("Failed to update")


    def get(self, addr, count):
        addr -= self.reg_start
        return self.regs[addr : addr + count]

    def print_all(self):
        for i in range(self.reg_start, self.reg_end):
            v = self.get(i,1)[0]
            print(f"{i}:\t{v}")

    def get_s32(self, addr):
        regs = self.get(addr, 2)
        logger.info(regs)
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
            self._modbus = pysolarmanv5.PySolarmanV5Async(ip, serial, port=port, auto_reconnect=True)

        except struct.error:
            raise exceptions.SerialInvalid("Invalid serial number provided")
        except pysolarmanv5.pysolarmanv5.NoSocketAvailableError:
            raise exceptions.ConnectionError("Cannot Connect")


        self.info_regs = SolisInfoRegs(self._modbus)

    async def _init(self):
        await self._modbus.connect()

    async def async_update(self):
        await self.info_regs.async_update()

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
        logger.debug("Battery Change Rate: %s", batt)
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

    @property
    def dc_voltage_1(self):
        return self.info_regs.get_u16(33049) / 10

    @property
    def dc_voltage_2(self):
        return self.info_regs.get_u16(33051) / 10
