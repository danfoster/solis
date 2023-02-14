import click

from .solis import Solis


@click.group()
@click.pass_context
@click.option("--ip", required=True)
@click.option("--serial", type=int, required=True)
@click.option("--port", type=int, default=8899)
def main(ctx, ip: str, serial: int, port: int):
    ctx.ensure_object(dict)
    ctx.obj["solis"] = Solis(ip, serial, port)


@main.command()
@click.pass_context
@click.option("--enable/--disable", default=True)
def charge(ctx, enable):
    ctx.obj["solis"].charge(enable)


@main.command()
@click.pass_context
def stats(ctx):
    solis = ctx.obj["solis"]
    batt = solis.batt_charge_rate

    print(f"Serial: {solis.serial}")
    print(f"DSP: {solis.sw_dsp_version}")
    if solis.charging:
        print(f"Battery charging: {batt} W")
    else:
        print(f"Battery discharging: {batt} W")

    print(f"Battery Level: {solis.batt_charge_level}%")
