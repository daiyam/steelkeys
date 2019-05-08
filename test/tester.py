#!/usr/bin/env python

# Activate the backlight one key at a time.

import keyboard
from time import sleep

MODEL = 'M800'
COLOR = 'ffffff'
DELAY = 0.1

from steelkeys.keyboard import Keyboard

kb = Keyboard(MODEL)

try:
	kb.open()
except:
	print('Can not access keyboard')
	sys.exit(1)

kb.disable()

print('Press space to start')

keyboard.wait('space')


for key in kb.listKeys():
	print(key)

	kb.pushConfig({key: {'color': COLOR}})

	sleep(DELAY)

	print('Press space to continue')

	keyboard.wait('space')
