#!/usr/bin/env python

import argparse
import json
import sys
from steelkeys.keyboard import Keyboard, HIDLibraryError, HIDNotFoundError, HIDOpenError, UnknownPresetError

VERSION = "0.1"

def main():
	parser = argparse.ArgumentParser(description='Configuration tool for SteelSeries RGB keyboards.')
	parser.add_argument('-v', '--version', action='store_true', help='Prints version and exits.')
	parser.add_argument('--list-models', action='store_true', help='List available keyboard models.')
	parser.add_argument('-m', '--model', action='store', help='Set keyboard model (see --list-models).')
	parser.add_argument('--list-presets', action='store_true', help='List available presets for the given keyboard model.')
	parser.add_argument('-p', '--preset', action='store', help='Use vendor preset (see --list-presets).')
	parser.add_argument('-c', '--config', action='store', metavar='FILEPATH', help='Loads the configuration file located at FILEPATH. Refer to the README for syntax.')
	parser.add_argument('-d', '--disable', action='store_true', help='Disable RGB lighting.')
	parser.add_argument('-j', '--json', action='store', help='Apply the given json as the configuration')

	args = parser.parse_args()

	if args.version:
		print("Version : %s" % VERSION)

	elif args.list_models:
		print("Available keyboard models are :")
		# for msi_models, _ in AVAILABLE_MSI_KEYMAPS:
		#     for model in msi_models:
		#         print(model)

		print("\nIf your keyboard is not in this list, use the closest one (with a keyboard layout as similar as possible).")
	else:

		# Parse keyboard model
		if not args.model:
			print("No keyboard model specified")
			sys.exit(1)

		try:
			kb = Keyboard(args.model)
		except UnknownModelError:
			print("Unknown model : %s" % args.model)
			sys.exit(1)

		if args.list_presets:
			presets = kb.listPresetKeys()

			if len(presets) == 0:
			    print("No presets available for %s." % args.model)
			else:
			    print("Available presets for %s:" % args.model)
			    for preset in presets:
			        print("\t- %s" % preset)
		else:

			# Loading keyboard
			try:
				kb.open()
			except HIDLibraryError as e:
				print("Cannot open HIDAPI library : %s. Make sure you have installed libhidapi on your system, then try running \"sudo ldconfig\" to regenerate library cache." % str(e))
				sys.exit(1)
			except HIDNotFoundError:
				print("No keyboards with a known product/vendor IDs were found.")
				sys.exit(1)
			except HIDOpenError:
				print("Cannot open keyboard. Possible causes :\n- You don't have permissions to open the HID device. Run this program as root, or give yourself read/write permissions to the corresponding /dev/hidraw*. If you have just installed this tool, reboot your computer for the udev rule to take effect.\n- USB device is not a HID device.")
				sys.exit(1)

			# If user has requested disabling
			if args.disable:
				kb.disable()

			# If user has requested a preset
			elif args.preset:
				try:
					kb.pushPreset(args.preset)
				except UnknownPresetError:
					print("Preset %s not found for model %s. Use --list-presets for available options" % (args.preset, args.model))
					sys.exit(1)

			# If user has requested to apply a config line
			elif args.json:
				try:
					kb.pushConfig(json.loads(args.json))
				except ConfigError as e:
					print("Error in the json : %s" % str(e))
					sys.exit(1)

			# If user has requested to load a config file
			elif args.config:
				print("Error reading config file")
				# try:
				# 	colors_map, warnings = load_config(args.config, msi_keymap)
				# except ConfigError as e:
				# 	print("Error reading config file : %s" % str(e))
				# 	sys.exit(1)

				# for w in warnings:
				# 		print("Warning :", w)

				# kb.set_colors(colors_map)

			# If user has not requested anything
			else:
				print("Nothing to do ! Please specify a preset, or a config file.")


if __name__ == '__main__':
	main()
