# import click
import asyncclick as click
import logging

from .solis import Solis
from .utils import setup_logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option("--ip", required=True)
@click.option("--serial", type=int, required=True)
@click.option("--port", type=int, default=8899)
async def main(ctx, ip: str, serial: int, port: int):
    setup_logging(False)
    ctx.ensure_object(dict)
    ctx.obj["solis"] = await Solis.create(ip, serial, port)


@main.command()
@click.pass_context
@click.option("--enable/--disable", default=True)
async def charge(ctx, enable):
    solis = ctx.obj["solis"]
    await solis.charge(enable)


@main.command()
@click.pass_context
async def stats(ctx):
    solis = ctx.obj["solis"]
    await solis.async_update()

    print(f"{'Serial:':>25} {solis.serial}")
    print(f"{'DSP:':>25} {solis.sw_dsp_version}")

    print(f"{'Battery Level:':>25} {solis.batt_charge_level}%")
    print(f"{'Battery Health:':>25} {solis.batt_health}%")
    print(f"{'DC volage 1:':>25} {solis.dc_voltage_1}V")
    print(f"{'DC volage 2:':>25} {solis.dc_voltage_2}V")
    print(f"{'Temperture:':>25} {solis.temperture}°C")
    print("-------")
    print(f"{'Power Generation Today:':>25} {solis.power_gen_today}Wh")
    print(f"{'Battery Charge Today:':>25} {solis.battery_charge_today}Wh")
    print(f"{'Battery Discharge Today:':>25} {solis.battery_discharge_today}Wh")
    print(f"{'House Load Today:':>25} {solis.house_load_today}Wh")
    print(f"{'Grid Imported Today:':>25} {solis.grid_imported_today}Wh")
    print(f"{'Grid Exported Today:':>25} {solis.grid_exported_today}Wh")
    print("------")
    print(f"{'Power Generation:':>25} {solis.power_generation}W")
    print(f"{'House Load:':>25} {solis.house_load}W")
    print(f"{'Backup Load:':>25} {solis.backup_load}W")
    print(f"{'Grid Usage:':>25} {solis.grid_usage}W")
    print(f"{'Battery charging:':>25} {solis.batt_charge_rate}W")
