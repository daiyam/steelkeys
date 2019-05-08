import yaml
import os
from time import sleep
import ctypes as ct
import re
from steelkeys.hidapi_types import set_hidapi_types

import binascii

BLACK = [0, 0, 0]
DELAY = 0.01

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

		for key, value in self._layout['keys'].items():
			region = value['region']

			if not region in regions:
				regions[region] = []

			regions[region].append((value['keycode'], BLACK))

		for region, data in regions.items():
			self.__sendFeatureReport(self.__makePackets(region, data))

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

		# prefix = self._layout['regions'][region]['prefix']

		k = 0
		for (keycode, rgb) in data:

			#fragment = rgb + [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, keycode]
			fragment = rgb + [0x00, 0x00, 0x00, 0x2c, 0x01, 0x00, 0x01, 0x00, keycode]

			packet += fragment

			k += 1

		repeat = self._layout['regions'][region]['repeat']
		while k < repeat:
			packet += fragment
			k += 1

		minKeys = self._layout['regions'][region]['minKeys']
		if k < minKeys:
			fragment = [0x00] * 12

			while k < minKeys:
				packet += fragment
				k += 1

		packet += ([0x00] * 6)
		#packet += [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x39]

		#print(binascii.hexlify(bytearray(packet)))

		return packet
	# }}}

	def __makePackets(self, region, data): # {{{

		l = len(data)
		maxKeys = self._layout['maxKeys']

		if l > maxKeys:
			packets = []
			i = 0

			while i < l:
				j = i + maxKeys - 1

				packets.append(self.__makePacket(region, data[i:j]))

				i += maxKeys

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

	def __prepareGroup(self, name, data, regions): # {{{

		for key in self._layout['groups'][name]:
			self.__prepareKey(key, data, regions)
	# }}}

	def __prepareKey(self, keycode, data, regions): # {{{

		key = self._layout['keys'][keycode]

		region = key['region']

		if not region in regions:
			regions[region] = []

		regions[region].append((key['keycode'], parseColor(data['color'])))
	# }}}

	def pushConfig(self, config): # {{{

		regions = {}

		for key, data in config.items():
			if key in self._layout['keys']:
				self.__prepareKey(key, data, regions)
			elif key in self._layout['groups']:
				self.__prepareGroup(key, data, regions)

		for region, data in regions.items():
			self.__sendFeatureReport(self.__makePackets(region, data))

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
