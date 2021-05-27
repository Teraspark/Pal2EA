#!/usr/bin/python3

#Pal2EA v2.4
import glob, os, sys, re
import lzss
import argparse, csv
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from pathlib import Path
from io import StringIO

"""
-	to do
+	WIP
*	Working
?	unsure/might return to later

*?	argparse
*	file input
-	file output
-	get palette from image

+	Error handling
+	Warning handling
Parsing
	*	read through file
	+	handle including other files
		+	prevent looping caused by including parent file
	-	parse apart entries into data
	*	decide on syntax for input files
	*	handle duplicate names
	-	handle user definitions
	-	consider if statements
Output
+	generating definition file
-	generate output files
"""

#File loading/saving functions
def askForFileIn(filedata=()):
	filedata += (("all files","*.*"),)
	file = askopenfilename(title="Open",filetypes=filedata)
	return Path(file)

def askForFileOut(filedata=()):
	filedata += (("all files","*.*"),)
	file = asksaveasfilename(title="Save As",filetypes=filedata)
	return Path(file)

def isValidFile(file):
	return file.is_file()

def getInputArgs():
	Tk().withdraw()
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-i","--input", type=Path, default='')
	parser.add_argument("--debug",action="store_true",help="start in debug mode")
	
	args = parser.parse_args()
	if not isValidFile(args.input):
		args.input = askForFileIn(((".txt files","*.txt"),))
	if not isValidFile(args.input):
		raise FileNotFoundError("invalid input file")
	
	return args

class palmeta:
	"""This object holds the meta data for the output that
	will be generated by pal2EA
	
	error
		If true, no output files will be generated
	errorlog
		list of the errors found in the input file(s)
	warnlog
		list of all the warnings detected in the input files(s)
		Warnings do not trigger the error flag
	"""
	
	EAfile = "Palette Installer.event" #name of generated EA installer
	setupfile = "Palette Setup.event" #
	compext = ".lzpal" #file extenstion of compressed output
	
	error = False
	curerror = False #if current entry has an error
	
	errorlog = []
	warnlog = []
	labelList = [] #ensure unique labels for each entry
	nodeList = []
	
	#folders = []
	
	def renameLabel(pnode,label=""):
		"""renameLavel(pnode,label)
			returns the label name as string
		append number to the end of the label
		if it already exists to ensure each label
		is unique.
		If label is not given, create a new label.
		"""
		n = 2
		#number to append on to end of label to ensure that there are no duplicate labels
		name = label
		
		#generate generic label if necessary
		if not name: name = 'PaletteLabel'
		
		while(label and name in self.labelList):
			name = label + str(n)
			n += 1
		else:
			#add new name to list of existing labels
			self.labelList.append(name)
		return name
		
	def addWarning(self, wtype, file=Path(), line=-1,text= ""):
		#fix this now that palfile is a thing
		log = wtype + ' warning: '
		if(file):
			log += str(file) + ':'
			if(line >= 0):
				log += ' line ' +str(line) + ':'
		log += text
		self.warnlog.append(log)
		return
	
	def addError(self, etype, file=Path(), line=-1,text=""):
		#fix this now that palfile is a thing
		self.error = True
		log = etype + ' warning: '
		if(file):
			log += str(file) + ':'
			if(line >= 0):
				log += ' line ' +str(line) + ':'
		log += text
		self.warnlog.append(log)
		
		return
	
	def addNode(self, node):
		self.nodeList.append(node)
		return
		
	def genOutput():
		"""create all the output files
		also prints out errors and warnings
		not files are output if errors were detected"""
		
		if(not self.error):
			#start to output files if there are no errors
			pass
		
		if(self.errorlog):
			for error in errorlog:
				print(error)
		if(self.warnlog):
			for warning in warnlog:
				print(warning)
		if((not self.errorlog) and (not self.warnlog)):
			print('No errors or warnings')
		elif(not self.errorlog):
			print('No errors detected')
		return
	

	
class palfile:
	meta = None
	#line number first line of current entry in file
	#curline = -1
	
	infile = None #file path to the input file being read
	indata = [] #the data
	
	#list of the file chain the current file was included
	#from to avoid endless include loops
	ancestors = ()
	
	def __init__(self,source,meta,parent=None):
		''' __init__(self,meta=None,parent=None)
		meta: palmeta
		parent: palfile
		'''
		self.infile = source
		self.meta = meta
		if(parent):
			self.ancestors = (parent,) + parent.ancestors
			# ancestors.append(parent)
			# ancestors.extend(parent.ancestors)
		return
	
	def isAncestor(self,file):
		"""ifAncestor(self,file)
			returns True or False
		check if passed file is part of the
		included file chain.
		"""
		return file in self.ancestors
	
	#FINISH THIS
	def parseFile(self):
		linenum = 1
		#subfunctions for primary commands
		def autofill(data):
			print('autofill ' + str(data))
			return
		def define(data):
			print('define ' + str(data))
			return
		def include(data):
			print('include ' + str(data))
			try:
				newfile = Path(data[0])
			except:
				self.meta.addError('Include',file=self.infile,line=linenum)
				return
			if newfile.isValidFile() and not self.isAncestor(newfile):
				newfile = palfile(newfile,self.meta,self)
				newfile.parseFile()
			else:
				self.meta.addError('Include',file=self.infile,line=linenum)
			return
		def newNode(data):
			newnode = palnode(source=self.infile,meta=self.meta)
			self.meta.addNode(newnode)
			print('newnode ' + str(data))
			return
		def message(data):
			print(str(self.infile)+':'+str(linenum)+':'+' '.join(data))
			return
		def write(data):
			self.output.append(' '.join(data))
			return
		commands = {
			'#auto': autofill,
			'#define': define,
			'#message': message,
			'#new': newNode,
			'#write': write
			}
		try:
			with self.infile.open('r') as f:
				#store file data as list of lines
				self.indata = f.readlines()
		except:
			self.meta.addError("File",file=self.infile)
		self.removeComments()
		#call meta for info on how to parse content of file
		while(self.indata):
			#skip line if blank
			if(self.indata[0].strip()):
				c, *args = list(csv.reader(StringIO(self.indata[0]),delimiter=' '))[0]
				
				if c in commands:
					commands[c](args)
				else:
					self.addError('definition',file=self.infile,line=linenum,text=str(data[0])+'is not defined')
			#remove line after is has been parsed
			self.indata.pop(0)
			linenum += 1
		return
	
		
	def removeComments(self):
		'''removeComments()
		remove single line "//comments" 
		and multi line "/* comments */"
		from file before input is parsed
		'''
		mlc = False
		#loop through every line and remove comments
		for lnum,text in enumerate(self.indata):
			if mlc:
				if '*/' in text:
					text = text[text.find('*/')+2:]
					mlc = False
				else: text = ''
			if not mlc:
				#remove single line comment
				if '//' in text:
					c = 0
					c = text.find('//')
					while(c >= 0):
						#check if comment is inside of quotes
						if not text[:c].count('"')%2:
							#remove everything after '//'
							text = text[:c]
						c = text.find('//',c+2)
				#remove multiline comment
				if '/*' in text:
					c = 0
					c = text.find('/*')
					while (c>=0):
						if not text[:c].count('"',0,c)%2:
							#check if comment ends in same line
							if '*/' in text[c+2:]:
								text = text[:c] + text[text.find('*/',c+2)+2:]
							else:
								text = text[:c]
								mlc = True
						c = text.find('/*',c+2)
					
			self.indata[lnum] = text
		if mlc:
			self.meta.addError("Comment",text="Multi line comment missing closing '*/'")
		return

class palnode:
	""" Handles the conversion of the data
	into objects for output"""
	#holds info relevant for a specfic entry in the file
	
	#point to palmeta
	meta = None
	
	#point to palfile that this palnode is part of
	sfile = None
	
	#file to be #included
	child = None
	
	#line of the file that this node is located at
	curline = -1
	
	#Name to use for both the palette dump and label for this entry
	name = ""
	
	#Type of palette (character,generic, etc.), affects the auto filling
	pytpe = ""
	
	#palette data
	palette = bytearray()
	
	#list of indices of which palettes to replace,
	#mainly to support setting generic palettes for battle animations
	plist = []
	
	#list of character to palette assignments
	slist = []
	
	repoint = ""
	at = ""
	
	#autofill stuff
	cflag = True #compress palette if true
	autod = 0 #autofill index
	auton = 0 #number of palettes
	autos = 0 #size of each palette
		
	def __init__(self,source=None,meta=None,child=None):
		self.sfile = source
		self.meta = meta
		self.child = child
		return
	
	def getChild(self):
		return self.child
	
	def parseEntry(self,entry,line=-1):
	#def getinfo(line): #parse line
		return
	
	def autofill(self,paldata):
	#''.join(paldata.split()) to get rid of whitespace
		pals = paldata.split('\n')
		pals = list(filter(None, pals)) #remove empty lines
		
		#remove all whitespace from each palette
		for z,x in enumerate(pals):
			pals[z] = ''.join(x.split())
			
		#check if default palette exists
		if(self.autod > self.auton):
			self.meta.addError("Autofill"," Default palette does not exist")
		elif(pals[self.autod].lower() == 'auto'):
			self.meta.addError("Autofill"," Default palette does not exist")
		else:
		#use autofill settings on missing palettes
			if(len(pals),self.auton):
				for x in range(len(pals),self.auton):
					pals.append(pals[self.autod])
			for p in range(0,self.auton):
				if(pals[p].lower() == 'auto'):
					pals[p] = pals[self.autod]
			contents = ''.join(pals)
			if(not contents):
				self.meta.addWarning("Empty Entry")
		try:
			contents = bytearray.fromhex(contents)
		except:
			self.meta.addError('Hex Conversion')
			contents = bytearray()
		return contents

#Input parsing functions

def palette_hex(paldata, auto, comp):
	pals = re.sub(r'\n\s*\n', '\n', paldata) #remove empty lines
	pals = pals.strip()
	if(comp):
		pals = pals.split('\n')
		pals = list(filter(None, pals)) #remove empty lines
		dindex = auto[0]
		amount = auto[1]
		length = auto[2]
		if (dindex > amount):
			#print('\t',"Autofill Error: Default palette does not exist")
			addError("Autofill", " Default palette does not exist")
			error = True
			#return or sys.exit()
		if (len(pals) < amount):
			for x in range(len(pals), amount):
				pals.append('auto')
		for p in range(0, amount):
			a = pals[p].find('auto')
			if (a >= 0):		
				pals[p] = pals[dindex]
			pals[p] = re.sub('[\s+]', '', pals[p])
		contents = "".join(pals)
	else:
		contents = re.sub('[\s+]', '', pals) #remove all whitespace
	
	try:
		contents = bytearray.fromhex(contents)
	except:
		addError("Hex Conversion")
		contents = bytearray() #return empty bytearray
	
	return contents

def lineNumber(p, data):
	lines = data[:p]
	return lines.count('\n') + 1

def is_hex(s):
	try:
		int(s, 16)
		return True
	except ValueError:
		return False

def generate(args):
	#initialize class
	#parse input file
	#create subfolder
	#generate output files
	palmain = palmeta()
	firstnode = palnode(child=args.input,meta=palmain)
	palmain.addNode(firstnode)
	start = palfile(args.input,palmain)
	start.parseFile()
	return

if __name__ == '__main__':
	print('pal2EA v2.4') #print current version
	try:
		z = getInputArgs() #parse command line arguments
	except:
		z = None
	if(z):
		generate(z) #
	
