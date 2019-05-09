import yaml
import os
from time import sleep
import ctypes as ct
import re
from steelkeys.hidapi_types import set_hidapi_types
import struct

import binascii

DELAY = 0.01

BLACK = [0, 0, 0]
LENGTH = 42
EMPTY_FRAGMENT = [0x00] * 12
CLOSING_FRAGMENT = [0x00] * 7

EFFECT_DISABLE = [0x64, 0x00, 0x00, 0x01]
EFFECT_REACTIVE = [0x00, 0x08]
EFFECT_STEADY = [0x2c, 0x01, 0x00, 0x01]

class ConfigError(Exception):
    pass

class HIDLibraryError(Exception):
	pass

class HIDNotFoundError(Exception):
	pass

class HIDOpenError(Exception):
	pass

class HIDSendError(Exception):
	pass

class UnknownModelError(Exception):
	pass

class UnknownPresetError(Exception):
	pass

def parseColor(color): # {{{
	if not isinstance(color, str):
		raise ConfigError('%s is not a string' % color)

	# Color in HTML notation
	if not re.fullmatch('^[0-9a-f]{6}$', color):
		raise ConfigError('%s is not a valid color' % color)

	return [int(color[i:i+2], 16) for i in [0, 2, 4]]
# }}}

class Keyboard:

	def __init__(self, model): # {{{

		path = os.path.join(os.path.dirname(__file__), 'models.yaml')
		models = yaml.load(open(path))

		model = model.lower()

		if not model in models:
			raise UnknownModelError(model)

		self._id = models[model]['id']

		path = os.path.join(os.path.dirname(__file__), 'layouts', models[model]['layout'] + '.yaml')
		self._layout = yaml.load(open(path))

		if 'presets' in self._layout:
			path = os.path.join(os.path.dirname(__file__), 'presets', self._layout['presets'] + '.yaml')
			self._presets = yaml.load(open(path))
		else:
			self._presets = {}
	# }}}

	def disable(self): # {{{

		regions = {}
		solos = []

		for key, value in self._layout['keys'].items():
			region = value['region']

			if 'solo' in value:
				solos.append({
					'region': region,
					'data': [(value['keycode'], BLACK, BLACK, EFFECT_STEADY) for i in range(value['solo'])]
				})
			else:
				if not region in regions:
					regions[region] = []

				regions[region].append((value['keycode'], BLACK, BLACK, EFFECT_DISABLE))

		for region, data in regions.items():
			self.__sendFeatureReport(self.__makePackets(region, data))

		for solo in solos:
			self.__sendFeatureReport(self.__makePackets(solo['region'], solo['data']))

		self.refresh()
	# }}}

	def listKeys(self): # {{{

		return self._layout['keys'].keys()
	# }}}

	def listPresetKeys(self): # {{{

		return self._presets.keys()
	# }}}

	def __makePacket(self, region, data): # {{{
		#print(region)
		#print(data)

		packet = [0x0e, 0x00, self._layout['regions'][region]['code'], 0x00]

		k = 0
		for (keycode, active, rest, effect) in data:

			fragment = active + rest + effect + [0x00, keycode]

			packet += fragment

			k += 1

		packet += EMPTY_FRAGMENT * (LENGTH - k)

		packet += CLOSING_FRAGMENT

		#print(binascii.hexlify(bytearray(packet)))

		return packet
	# }}}

	def __makePackets(self, region, data): # {{{

		l = len(data)
		max = LENGTH

		if l > LENGTH:
			packets = []
			i = 0

			while i < l:
				j = i + LENGTH

				packets.append(self.__makePacket(region, data[i:j]))

				i += LENGTH

			return packets
		else:
			return [self.__makePacket(region, data)]
	# }}}

	def open(self): # {{{

		# Locating HIDAPI library
		s = os.popen('ldconfig -p').read()
		path_matches = re.findall('/.*libhidapi-hidraw\\.so.+', s)
		if len(path_matches) == 0:
			raise HIDLibraryError('Cannot locate the hidapi library')

		lib_path = path_matches[0]

		if not os.path.exists(lib_path):
			raise HIDLibraryError('ldconfig reports HIDAPI library at %s but file does not exists.' % lib_path)

		# Loading HIDAPI library
		self._hidapi = ct.cdll.LoadLibrary(lib_path)
		set_hidapi_types(self._hidapi)

		# Checking if the USB device corresponding to the keyboard exists
		vid_str = hex(self._id['vendor'])[2:].zfill(4)
		pid_str = hex(self._id['product'])[2:].zfill(4)
		id_str = vid_str + ':' + pid_str
		s = os.popen('lsusb').read()
		if s.find(id_str) == -1:
			raise HIDNotFoundError

		self._device = self._hidapi.hid_open(self._id['vendor'], self._id['product'], ct.c_wchar_p(0))

		if self._device is None:
			raise HIDOpenError
	# }}}

	def __prepare(self, key, data, config, regions, solos): # {{{

		if isinstance(data, str):
			self.__prepare(key, config[data], config, regions, solos)
		else:
			if key in self._layout['keys']:
				self.__prepareKey(key, data, regions, solos)
			elif key in self._layout['groups']:
				self.__prepareGroup(key, data, regions, solos)
	# }}}

	def __prepareGroup(self, name, config, regions, solos): # {{{

		for key in self._layout['groups'][name]:
			self.__prepareKey(key, config, regions, solos)
	# }}}

	def __prepareKey(self, keycode, config, regions, solos): # {{{

		key = self._layout['keys'][keycode]

		region = key['region']

		if not 'fx' in config or config['fx'] == 'steady':
			color = parseColor(config['color'])

			data = (key['keycode'], color, BLACK, EFFECT_STEADY)

		elif config['fx'] == 'disable':
			data = (key['keycode'], BLACK, BLACK, EFFECT_STEADY)

		elif config['fx'] == 'reactive':
			active = parseColor(config['active'])
			rest = parseColor(config['rest'])

			speed = 300
			if 'speed' in config:
				speed = config['speed']

			effect = list(struct.unpack('bb', struct.pack('<h', speed))) + EFFECT_REACTIVE

			data = (key['keycode'], rest, active, effect)

		if 'solo' in key:
			solos.append({
				'region': region,
				'data': [data for i in range(key['solo'])]
			})
		else:
			if not region in regions:
				regions[region] = []

			regions[region].append(data)
	# }}}

	def pushConfig(self, config): # {{{

		regions = {}
		solos = []

		for key, data in config.items():
			self.__prepare(key, data, config, regions, solos)

		for region, data in regions.items():
			self.__sendFeatureReport(self.__makePackets(region, data))

		for solo in solos:
			self.__sendFeatureReport(self.__makePackets(solo['region'], solo['data']))

		self.refresh()
	# }}}

	def pushPreset(self, preset): # {{{

		if not preset in self._presets:
			raise UnknownPresetError(preset)

		self.__sendFeatureReport([bytearray.fromhex(data) for data in self._presets[preset]])

		self.refresh()
	# }}}

	def refresh(self): # {{{

		self.__sendOutputReport([0x09] + [0x00] * 63)
	# }}}

	def __sendFeatureReport(self, packets): # {{{

		for data in packets:
			ret = self._hidapi.hid_send_feature_report(self._device, bytes(data), len(data))

			if ret == -1 or ret != len(data):
				raise HIDSendError("HIDAPI returned error upon sending feature report to keyboard.")

			# The RGB controller derps if commands are sent too fast.
			sleep(DELAY)
	# }}}

	def __sendOutputReport(self, data): # {{{

		ret = self._hidapi.hid_write(self._device, bytes(data), len(data))

		# The RGB controller derps if commands are sent too fast.
		sleep(DELAY)

		if ret == -1 or ret != len(data):
			raise HIDSendError("HIDAPI returned error upon sending output report to keyboard.")
	# }}}
