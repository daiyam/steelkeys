import yaml
import os
from time import sleep
import ctypes as ct
import re
from steelkeys.hidapi_types import set_hidapi_types

import binascii

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

class Keyboard:

	def __init__(self, model):

		path = os.path.join(os.path.dirname(__file__), 'models.yaml')
		models = yaml.load(open(path))

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

	def disable(self):

		regions = {}

		for key, value in self._layout['keys'].items():
			region = value['region']

			if not region in regions:
				regions[region] = []

			regions[region].append(value['keycode'])

		black = [0, 0, 0]

		for region, keycodes in regions.items():
			data = dict(zip(keycodes, [black] * len(keycodes)))

			self.sendFeatureReport(self.makePacket(region, data))

		self.refresh()

	def listKeys(self):

		return self._layout['keys'].keys()

	def listPresetKeys(self):

		return self._presets.keys()

	def makePacket(self, region, data):
		#print(region)
		#print(data)

		packet = [0x0e, 0x00, self._layout['regions'][region]['code'], 0x00]

		# prefix = self._layout['regions'][region]['prefix']

		k = 0
		for keycode, rgb in data.items():

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

		#packet += ([0x00] * 6)
		packet += [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x39]

		#print(binascii.hexlify(bytearray(packet)))

		return packet

	def open(self):

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

	def prepareConfig(self, config, regions):

		print(config)

		if not config['key'] in self._layout['keys']:
			raise ConfigError('%s is not a valid keycode.' % config['key'])

		# Color in HTML notation
		if not re.fullmatch("^[0-9a-f]{6}$", config['color']):
			raise ConfigError("%s is not a valid color" % config['color'])

		key = self._layout['keys'][config['key']]

		region = key['region']

		if not region in regions:
			regions[region] = {}

		regions[region][key['keycode']] = [int(config['color'][i:i+2], 16) for i in [0, 2, 4]]

	def pushConfig(self, config):

		regions = {}

		if isinstance(config, list):
			for c in config:
				self.prepareConfig(c, regions)

		elif isinstance(config, dict):
			self.prepareConfig(config, regions)

		for region, data in regions.items():
			self.sendFeatureReport(self.makePacket(region, data))

		self.refresh()

	def pushPreset(self, preset):

		if not preset in self._presets:
			raise UnknownPresetError(preset)

		for data in self._presets[preset]:
			self.sendFeatureReport(bytearray.fromhex(data))

		self.refresh()

	def refresh(self):

		self.sendOutputReport([0x09] + [0x00] * 63)

	def sendFeatureReport(self, data):

		ret = self._hidapi.hid_send_feature_report(self._device, bytes(data), len(data))

		# The RGB controller derps if commands are sent too fast.
		sleep(DELAY)

		if ret == -1 or ret != len(data):
			raise HIDSendError("HIDAPI returned error upon sending feature report to keyboard.")

	def sendOutputReport(self, data):

		ret = self._hidapi.hid_write(self._device, bytes(data), len(data))

		# The RGB controller derps if commands are sent too fast.
		sleep(DELAY)

		if ret == -1 or ret != len(data):
			raise HIDSendError("HIDAPI returned error upon sending output report to keyboard.")
