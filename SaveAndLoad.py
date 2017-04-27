# -*- coding: utf-8 -*-

import codecs
import json

# 一个一行保存对象
def save(outFile,saveObject): 
	out = codecs.open(outFile, "w", "utf-8")
	for x in saveObject:
		out.write(json.dumps(x))
		out.write("\n")

# 读取保存在一个文件里的对象，一行一个
def load(inFile,numberOfObject):
	returnObject = []
	inList = open(inFile, "r").readlines()
	i = 0
	for i in range(numberOfObject):
		x = json.loads(inList[i])
		returnObject.append(x)
	return returnObject
