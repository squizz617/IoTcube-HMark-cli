#! /usr/bin/env python2

import sys
import os
import time
from hashlib import md5
from multiprocessing import Pool
import argparse
import parseutility

import version
import get_cpu_count

""" GLOBALS """
currentVersion = version.version

def parseFile_shallow_multi(f):
	functionInstanceList = parseutility.parseFile_shallow(f, "GUI")
	return (f, functionInstanceList)

def parseFile_deep_multi(f):
	functionInstanceList = parseutility.parseFile_deep(f, "GUI")
	return (f, functionInstanceList)


def generate(directory, absLevel):
	progress = 0
	if directory.endswith('/'):
		directory = directory[:-1]
	proj = directory.replace('\\', '/').split('/')[-1]
	timeIn = time.time()
	numFile = 0
	numFunc = 0
	numLine = 0

	projDic = {}
	hashFileMap = {}

	print "Loading source files... This may take a few minutes."

	fileList = parseutility.loadSource(directory)
	numFile = len(fileList)

	if numFile == 0:
		print "Error: Failed loading source files. Check if you selected proper directory, or if your project contains .c or .cpp files."
	else:
		print "Load complete. Generating hashmark..."

		if absLevel == 0:
			func = parseFile_shallow_multi
		else:
			func = parseFile_deep_multi

		cpu_count = get_cpu_count.get_cpu_count()
		if cpu_count != 1:
			cpu_count -= 1

		pool = Pool(processes = cpu_count)
		for idx, tup in enumerate(pool.imap_unordered(func, fileList)):
			f = tup[0]
			functionInstanceList = tup[1]

			fullName = proj + f.split(proj, 1)[1]
			pathOnly = f.split(proj, 1)[1][1:]
			progress = 100*(float)(idx + 1) / numFile
			sys.stdout.write("\r%.2f%% %s                         " % (progress, fullName))
			sys.stdout.flush()

			numFunc += len(functionInstanceList)

			if len(functionInstanceList) > 0:
				numLine += functionInstanceList[0].parentNumLoc

			for f in functionInstanceList:
				f.removeListDup()
				path = f.parentFile
				absBody = parseutility.abstract(f, absLevel)[1]
				absBody = parseutility.normalize(absBody)
				funcLen = len(absBody)

				if funcLen > 50:
					hashValue = md5(absBody).hexdigest()

					try:
						projDic[funcLen].append(hashValue)
					except KeyError:
						projDic[funcLen] = [hashValue]
					try:
						hashFileMap[hashValue].extend([pathOnly, f.funcId])
					except KeyError:
						hashFileMap[hashValue] = [pathOnly, f.funcId]
				else:
					numFunc -= 1 # decrement numFunc by 1 if funclen is under threshold

		print "\nHash index successfully generated."
		print "Saving hash index to file...",

		try:
			os.mkdir("hidx")
		except:
			pass
		packageInfo = str(currentVersion) + ' ' + str(proj) + ' ' + str(numFile) + ' ' + str(numFunc) + ' ' + str(numLine) + '\n'
		with open("hidx/hashmark_" + str(absLevel) + "_" + proj + ".hidx", 'w') as fp:
			fp.write(packageInfo)

			for key in sorted(projDic):
				fp.write(str(key) + '\t')
				for h in list(set(projDic[key])):
					fp.write(h + '\t')
				fp.write('\n')

			fp.write('\n=====\n')

			for key in sorted(hashFileMap):
				fp.write(str(key) + '\t')
				for f in hashFileMap[key]:
					fp.write(str(f) + '\t')
				fp.write('\n')

		timeOut = time.time()
		print "(Done)"
		print "Elapsed time: %.02f sec." % (timeOut - timeIn)
		print str(numFile), "Files, ", str(numFile), "Functions, ", str(numLine), "Lines of code."
		print ""


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("-p", "--path", required = True,
		help = "Destination path")
	ap.add_argument("-lv", "--level", required = True,
		help = "Abstraction level[0~4]")
	args = vars(ap.parse_args())

	if args['level'].isdigit():
		lv = int(args['level'])
		if lv == 0 or lv == 4:
			generate(args['path'],lv)
		else:
			print "[Error] Wrong level selection."
			print "Abstraction level: 0 (no abstraction) or 4 (full abstraction)"
			sys.exit()
	else:
		print "USAGE: python hmark-cli.py -p [/path/to/program] -lv [Abstraction Level]"
		print "Abstraction level: 0 (no abstraction) or 4 (full abstraction)"
		sys.exit()


""" EXECUTE """
if __name__ == "__main__":
	main()
