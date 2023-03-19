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
    ctx.obj["solis"] = Solis(ip, serial, port)
    await ctx.obj["solis"]._init()


@main.command()
@click.pass_context
@click.option("--enable/--disable", default=True)
async def charge(ctx, enable):
    await ctx.obj["solis"].charge(enable)


@main.command()
@click.pass_context
async def stats(ctx):
    solis = ctx.obj["solis"]
    await solis.async_update()
    batt = solis.batt_charge_rate

    print(f"Serial: {solis.serial}")
    print(f"DSP: {solis.sw_dsp_version}")
    if solis.charging:
        print(f"Battery charging: {batt} W")
    else:
        print(f"Battery discharging: {batt} W")

    print(f"Battery Level: {solis.batt_charge_level}%")
    print(f"DC volage 1: {solis.dc_voltage_1}V")
