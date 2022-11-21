import click

from .solis import Solis


@click.group()
@click.pass_context
@click.option("--ip")
@click.option("--serial", type=int)
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
    ctx.obj["solis"].stats()
