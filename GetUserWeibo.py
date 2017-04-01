# -*- coding: utf-8 -*-

import codecs
from bs4 import BeautifulSoup

inList = open("72.list", "r").readlines();
print(len(inList))

for inFileName in inList:
	inFile = codecs.open(inFileName[:len(inFileName)-1]+".html", "r", "utf-8")
	content = inFile.read()
	inFile.close()
	soup = BeautifulSoup(content, "html5lib")
	print(soup.title.string)
	usefulInfo = soup.find_all("div", "c")
	print(usefulInfo[0].img.attrs['src'])
	tags="";
	for s in usefulInfo[2].stripped_strings:
		s=s.replace("：",":")
		if (s.find("标签")!=-1 or s.find(":")==-1):
			if (s.find(">>")==-1):
				tags+=s+" "
		else:
			print(s)
	print(tags)
	for i in range(3,len(usefulInfo)-3):
		for x in usefulInfo[i].stripped_strings:
			print(x.replace("\xa0"," "))
	for x in usefulInfo[len(usefulInfo)-3].stripped_strings:
		if (x.find("互联网")!=-1):
			print(x[len("互联网:http://weibo.com/"):])
# inFile = codecs.open("72.html", "r", "utf-8")
# content = inFile.read()
# inFile.close()
# soup = BeautifulSoup(content, "html5lib")
# l = soup.find_all("div", "c")
# l = soup.select("[.c]")
# l[0].img.attrs['alt']
# l[0].img.attrs['src']

# print(soup.title.string)

# outFile = codecs.open("72.out", "w", "utf-8")
# outFile.write(soup.title.string)
# outFile.close()