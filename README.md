# Solis

This is a Python module to interact with Solis Invertors connected via the Solarman v5 data loggers.

It builds on top of the [pysolarmanv5](https://github.com/jmccrohan/pysolarmanv5/) module to provide structured data output that can be consumed without needing to the know the registers and data formats of the underlying device.


## CLI Usage

```
Usage: solis [OPTIONS] COMMAND [ARGS]...

Options:
  --ip TEXT         [required]
  --serial INTEGER  [required]
  --port INTEGER
  --help            Show this message and exit.
```

### Showing stats

```
$ solis --ip 10.42.2.145 --serial xxxx stats
                  Serial: xxxx
                     DSP: 37
           Battery Level: 75%
          Battery Health: 100%
             DC volage 1: 4.2V
             DC volage 2: 4.0V
              Temperture: 38.5°C
-------
  Power Generation Today: 20400Wh
    Battery Charge Today: 3300Wh
 Battery Discharge Today: 4400Wh
        House Load Today: 10100Wh
     Grid Imported Today: 4000Wh
     Grid Exported Today: 15000Wh
------
        Power Generation: 0W
              House Load: 276W
             Backup Load: 0W
              Grid Usage: 3W
        Battery charging: -448W
```

### Setting charging from grid

```
$ solis --ip 10.42.2.145 --serial xxxxx charge
Enabling charging from grid
```

```
$ solis --ip 10.42.2.145 --serial xxxxx charge --disable
Disabling charging from grid
```

## Module usage

Due to the overhead of the modbus protocol of reading a small number of registers each time, the module has been designed to read all registers at once using the `Solis.async_update()` method, then various properties provide formatted access to relavant registers. e.g.

```
solis = await Solis.create(ip, serial, port)
await solis.async_update()
print(solis.bastt_change_level)
```

See solis.py for exposed registers.