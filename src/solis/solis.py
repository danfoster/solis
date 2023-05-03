"""
Module for managing Data from Solis Inverters
"""
import struct
import logging
import traceback
import asyncio

import pysolarmanv5
from . import exceptions

REG_ENERGY_CONTROL = 43110
REG_CHARGING = 33135

REG_INFO_START = 33000
REG_INFO_END = 33286

logger = logging.getLogger(__name__)


class SolisInfoRegs:
    """
    Manages access to Solis Information Registers
    """

    def __init__(self, modbus):
        self.modbus = modbus
        self.reg_start = 33000
        self.reg_end = 33286
        self.regs = [None] * self.reg_len

    @property
    def reg_len(self):
        """
        The Length of the registers block
        """
        return self.reg_end - self.reg_start

    async def get_regs(self):
        """
        Get all info registers in as few modbus calls as possible
        and store them for acccess later
        """
        regs = await self.modbus.read_input_registers(self.reg_start, 100)
        regs += await self.modbus.read_input_registers(self.reg_start + 100, 100)
        regs += await self.modbus.read_input_registers(
            self.reg_start + 200, self.reg_len - 200
        )
        return regs

    async def async_update(self):
        """
        Updates all info registers, with a retry mechanism.
        """
        count = 10
        logger.debug("Starting Update")
        for i in range(1, count + 1):
            await asyncio.sleep(i - 1)
            try:
                self.regs = await self.get_regs()
                logger.debug("Finishing Update")
                return
            except pysolarmanv5.V5FrameError as err:
                logger.info("[%s/%s] Error Updating: %s", i, count, err)
                logger.debug(traceback.format_exc())
                continue
            except struct.error as err:
                logger.info("[%s/%s] Error Updating: %s", i, count, err)
                logger.debug(traceback.format_exc())
                continue
            except ConnectionResetError as err:
                logger.info("[%s/%s] Error Updating: %s", i, count, err)
                logger.debug(traceback.format_exc())
                continue
            except TimeoutError as err:
                logger.info("[%s/%s] Error Updating: %s", i, count, err)
                logger.debug(traceback.format_exc())
                continue
            except pysolarmanv5.NoSocketAvailableError as err:
                logger.info("[%s/%s] Error Updating: %s", i, count, err)
                logger.debug(traceback.format_exc())
                await self.modbus.connect()
                continue

        raise exceptions.UpdateError("Failed to update")

    def get(self, addr, count):
        """
        Returns a number of info registers
        """
        addr -= self.reg_start
        return self.regs[addr : addr + count]

    def get_s32(self, addr):
        """
        Gets 2 registers (32 bits) at addr and returns it as
        an signed integer
        """
        regs = self.get(addr, 2)
        data = regs[0].to_bytes(2, "big") + regs[1].to_bytes(2, "big")
        result = int.from_bytes(data, "big", signed=True)
        return result

    def get_u16(self, addr):
        """
        Get 1 register (16 bits) at addr and return it as
        an unsigned integer
        """
        return self.get(addr, 1)[0]

    def get_ascii(self, addr, count):
        """
        Gets n-registers and returns it as an ASCII string.
        Where each 16 bit register represents 2 chars.
        """
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
    """
    Main class for Managing the Solis Inverter
    """

    @classmethod
    async def create(cls, ipaddr: str, serial: int, port: int = 8899):
        """
        Factory method for creating the object via a async
        co-routine.
        Use instead of the normal contructor.
        """
        self = cls(ipaddr, serial, port)
        await self._modbus.connect()
        return self

    def __init__(self, ipaddr: str, serial: int, port: int = 8899):
        self._serial = serial
        try:
            self._modbus = pysolarmanv5.PySolarmanV5Async(
                ipaddr, serial, port=port, auto_reconnect=True
            )

        except struct.error as err:
            raise exceptions.SerialInvalid("Invalid serial number provided") from err
        except pysolarmanv5.pysolarmanv5.NoSocketAvailableError as err:
            raise exceptions.ConnectionError("Cannot Connect") from err

        self.info_regs = SolisInfoRegs(self._modbus)

    async def async_update(self):
        await self.info_regs.async_update()

    async def charge(self, enable: bool):
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
        await self._modbus.write_holding_register(REG_ENERGY_CONTROL, value=value)

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
        """
        Battery Charge(+)/Discharge(-) rate (W)
        """
        batt = self.info_regs.get_s32(33149)
        if not self.charging:
            batt = -batt
        return batt

    @property
    def batt_charge_level(self):
        """
        Battery Charge Level (%)
        """
        return self.info_regs.get_u16(33139)

    @property
    def batt_health(self):
        return self.info_regs.get_u16(33140)

    @property
    def serial(self):
        """
        Serial Number
        """
        return self.info_regs.get_ascii(33004, 15)

    @property
    def sw_dsp_version(self):
        """
        DSP Software Version
        """
        return self.info_regs.get_u16(33001)

    @property
    def dc_voltage_1(self):
        return self.info_regs.get_u16(33049) / 10

    @property
    def dc_voltage_2(self):
        return self.info_regs.get_u16(33051) / 10

    @property
    def temperture(self):
        """
        Temperture of the Inverter (degress C)
        """
        return self.info_regs.get_u16(33093) / 10

    @property
    def power_gen_today(self):
        """
        Power Generation Today (Wh)
        """
        return self.info_regs.get_u16(33035) * 100

    @property
    def battery_charge_today(self):
        """
        Battery chanrge today (Wh)
        """
        return self.info_regs.get_u16(33163) * 100

    @property
    def battery_discharge_today(self):
        """
        Battery discharge today (Wh)
        """
        return self.info_regs.get_u16(33167) * 100

    @property
    def house_load_today(self):
        """
        Load today (Wh)
        """
        return self.info_regs.get_u16(33179) * 100

    @property
    def grid_imported_today(self):
        """
        Power imported today (Wh)
        """
        return self.info_regs.get_u16(33171) * 100

    @property
    def grid_exported_today(self):
        """
        Power exported today (Wh)
        """
        return self.info_regs.get_u16(33175) * 100

    @property
    def power_generation(self):
        """
        Generation (W)
        """
        return self.info_regs.get_s32(33057)

    @property
    def house_load(self):
        """
        Load from the House (W)
        """
        return self.info_regs.get_u16(33147)

    @property
    def backup_load(self):
        """
        Load on the Emergancy supply (W)
        """
        return self.info_regs.get_u16(33148)

    @property
    def grid_usage(self):
        """
        Usage from the grid / export (W)
        """
        return self.info_regs.get_s32(33130)
