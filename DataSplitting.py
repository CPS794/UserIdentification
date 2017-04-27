# -*- coding: utf-8 -*-

import codecs
import json
import random
import SaveAndLoad
import Const

if __name__ == "__main__":
	inFile = Const.PATH + Const.FILE_NAME + ".list"
	inList = open(inFile, "r").readlines()
	userAmount = len(inList)
	trainingAmount = int(userAmount * Const.TRAINING_PERCENTAGE)
	testAmount = userAmount - trainingAmount
	users = []
	for user in inList:
		users.append(user[:len(user)-1])

	for x in range(Const.NUMBER_OF_TEST):
		random.shuffle(users)
		fname = Const.PATH + Const.FILE_NAME + "/" + Const.FILE_NAME + "_" + str(x)
		SaveAndLoad.save(fname + "_S"+".in", [users[:trainingAmount]])
		SaveAndLoad.save(fname + "_T"+".in", [users[trainingAmount:]])
