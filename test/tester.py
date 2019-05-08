#!/usr/bin/env python

import keyboard

MODEL = 'm800'
COLOR = 'ffffff'

from steelkeys.keyboard import Keyboard

kb = Keyboard(MODEL)

try:
	kb.open()
except:
	print('Can not access keyboard')
	sys.exit(1)

for key in kb.listKeys():
	print(key)

	kb.pushConfig({'key': key, 'color': COLOR})

	print('Press space to continue')

	keyboard.wait('space')
