[steelkeys](https://github.com/daiyam/steelkeys)
================================================

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

Configuration tool for SteelSeries RGB keyboards.

Installation
------------

```
git clone https://github.com/daiyam/steelkeys.git
cd steelkeys
sudo python3 setup.py install
```

Command-line options
--------------------

```
usage: steelkeys [-h] [-v] [--list-models] [-m MODEL] [--list-presets]
                 [-p PRESET] [-c FILEPATH] [-d] [-j JSON]

configuration tool for SteelSeries RGB keyboards.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Prints version and exits.
  --list-models         List available keyboard models.
  -m MODEL, --model MODEL
                        Set keyboard model (see --list-models).
  --list-presets        List available presets for the given keyboard model.
  -p PRESET, --preset PRESET
                        Use vendor preset (see --list-presets).
  -c FILEPATH, --config FILEPATH
                        Loads the configuration file located at FILEPATH.
                        Refer to the README for syntax.
  -d, --disable         Disable RGB lighting.
  -j JSON, --json JSON  Apply the given json as the configuration
```

Compatibility
-------------

| Model                 | Code    | Effects                    |
| --------------------- | ------- | -------------------------- |
| SteelSeries Apex M800 | M800    | steady, reactive, disable  |

Requirements
------------

* Python 3.4+
* setuptools
  * **Archlinux** : `# pacman -S python-setuptools`
  * **Ubuntu** : `# apt install python3-setuptools`
* libhidapi 0.8+
  * **Archlinux** : `# pacman -S hidapi`
  * **Ubuntu** : `# apt install libhidapi-hidraw0`

Permissions
-----------

**IMPORTANT** : You need to have read/write access to the HID interface of your keyboard.

Usage
-----

```
steelkeys -m <model> -p <preset>
```
(see `--list-models` for available models)
(see `--list-presets` for available presets)

**or**

```
steelkeys -m <model> -c <path to your configuration file>
```

**or**

```
steelkeys -m <model> -j <configuration in JSON format>
```

#### Examples

```
sudo steelkeys -m M800 -p disco
```

```
sudo steelkeys -m M800 -j '{"all":{"color":"00ff00"}}'
```

Configuration file
------------------

The configuration can be either a JSON file or a YAML file.

### JSON

```json
{
  "all": {
    "fx": "reactive",
    "active": "ff0040",
    "rest": "ffffff",
    "speed": 300
  },
  "logo": {
    "fx": "disable"
  },
  "m0": {
    "fx": "reactive",
    "active": "80ff20",
    "rest": "0000ff",
    "speed": 300
  },
  "m4": "m0",
  "m5": "m0",
  "m1": {
    "fx": "reactive",
    "active": "80ff20",
    "rest": "ffff00",
    "speed": 300
  },
  "m2": "m1",
  "m3": "m1"
}
```

### YAML

```yaml
all:
  fx: reactive
  active: ff0040
  rest: ff0000
  speed: 300
logo:
  fx: disable
m0:
  fx: reactive
  active: 80ff20
  rest: ff0040
  speed: 300
m4: m0
m5: m0
m1:
  fx: reactive
  active: 80ff20
  rest: '404040'
  speed: 300
m2: m1
m3: m1
```

Thanks
------

I would like to thanks [Robin Lange](https://github.com/Askannz) for his project [msi-perkeyrgb](https://github.com/Askannz/msi-perkeyrgb) which this current project is based on.

License
-------

[MIT](http://www.opensource.org/licenses/mit-license.php) &copy; Baptiste Augrain