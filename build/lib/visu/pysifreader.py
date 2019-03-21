# coding: latin-1

# Licence.txt from original archive:
#	Copyright (c) 2006, Marcel Leutenegger
#	All rights reserved.
#
#	Redistribution and use in source and binary forms, with or without 
#	modification, are permitted provided that the following conditions are 
#	met:
#
#	    * Redistributions of source code must retain the above copyright 
#	      notice, this list of conditions and the following disclaimer.
#	    * Redistributions in binary form must reproduce the above copyright 
#	      notice, this list of conditions and the following disclaimer in 
#	      the documentation and/or other materials provided with the distribution
#	    * Neither the name of the Ecole Polytechnique Fédérale de Lausanne,
#	      Laboratoire d'Optique Biomédicale nor the names of its contributors may
#	      be used to endorse or promote products derived from this software
#	      without specific prior written permission.
#	      
#	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
#	AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
#	IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
#	ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
#	LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
#	CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
#	SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
#	INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
#	CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
#	ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
#	POSSIBILITY OF SUCH DAMAGE.

# pysifreader: Read Andor SIF multi-channel image file.
#
# Date: 23nd October, 2009
# Version: 1.0.1
# History:
#  1.0   -- 22/10/09 -- Initial release
#  1.0.1 -- 23/10/09 -- Streamlined and made code more portable
#
# Usage:
#     [data, back, ref] = SIFread(filename)
#
# Synopsis:
#     Read the image data, background and reference from file.
#     Return the image data, background and reference in variables of type SIFimage.
#
# Module pysifreader methods:
#  SIFread(filename)       Reads the file and returns the image data
#
# SIFimage methods:
#  .printInfo()            Prints all the available information (see below)
#
# SIFimage Properties:
#  .temperature            CCD temperature [deg. C]
#  .exposureTime           Exposure time [s]
#  .cycleTime              Time per full image take [s]
#  .accumulateCycles       Number of accumulation cycles
#  .accumulateCycleTime    Time per accumulated image [s]
#  .stackCycleTime         Interval in image series [s]
#  .pixelReadoutTime       Time per pixel readout [s]
#  .gainDAC                DAC gain
#  .detectorType           CCD type
#  .detectorSize           Number of read CCD pixels [x,y]
#  .seqNum                 Sequence number (0=none, 1=data, 2=background, 3=reference)
#  .fileName               Original file name
#  .shutterTime            Time to open/close the shutter [s]
#  .frameAxis              Axis unit of CCD frame
#  .dataType               Type of image data
#  .imageAxis              Axis unit of image
#  .imageArea              Image limits [x1,y1,first image; x2,y2,last image]
#  .frameArea              Frame limits [x1,y1; x2,y2]
#  .frameBins              Binned pixels [x,y]
#  .timeStamp              Time stamp in image series
#  .imageData              Image data (x,y,t)

# Note from Marcel Leutenegger:
#
#  The file format was reverse engineered by identifying known
#  information within the corresponding file. There are still
#  non-identified regions left over but the current summary is
#  available on request.
#

# Original MATLAB code by: © Marcel Leutenegger, November 2008
#  http://www.mathworks.com/matlabcentral/fileexchange/11224
# Ported to python by André Xuereb, October 2009
#  <andre.xuereb@soton.ac.uk>

class SIFimage:
#	def printInfo(self):
#		print ('Temperature: %d deg. C' % self.temperature)
#		print 'Exposure time: %f s' % self.exposureTime
#		print 'Time per full image take: %f s' % self.cycleTime
#		print 'Number of accumulation cycles: %d' % self.accumulateCycles
#		print 'Time per accumulated image: %f s' % self.accumulateCycleTime
#		print 'Interval in image series: %f s' % self.stackCycleTime
#		print 'Time per pixel readout: %f s' % self.pixelReadoutTime
#		print 'DAC gain: %f' % self.gainDAC
#		print 'Time to open/close the shutter: %f s/%f s' % (self.shutterTime[0], self.shutterTime[1])
#		print
#		print 'CCD type: %s' % self.detectorType
#		print 'Number of read CCD pixels (x, y): (%d, %d)' % (self.detectorSize[0], self.detectorSize[1])
#		print
#		print 'File name: %s' % self.fileName
#		print 'Sequence number: %d' % self.seqNum
#		print 'Axis unit of CCD frame: %s' % self.frameAxis
#		print 'Type of image data: %s' % self.dataType
#		print 'Axis unit of image: %s' % self.imageAxis
#		print 'Time stamp in image series: %d' % self.timeStamp
#		print
#		print 'Binned pixels (x, y): (%d, %d)' % (self.frameBins[0], self.frameBins[1])
#		print 'Frame limits (x1, y1; x2, y2): (%d, %d; %d, %d)' % (self.frameArea[0][0], self.frameArea[0][1], self.frameArea[1][0], self.frameArea[1][1])
#		print 'Image limits (x1, y1, first image; x2, y2, last image): (%d, %d, %d; %d, %d, %d)' % (self.imageArea[0][0], self.imageArea[0][1], self.imageArea[0][2], self.imageArea[1][0], self.imageArea[1][1], self.imageArea[1][2])

	def __init__(self):
		from pylab import array as p_array
		self.temperature = 0
		self.exposureTime = 0.
		self.cycleTime = 0.
		self.accumulateCycleTime = 0.
		self.accumulateCycles = 0.
		self.stackCycleTime = 0.
		self.pixelReadoutTime = 0.
		self.gainDAC = 0.
		self.seqNum = 0
		self.shutterTime = [0., 0.]
		self.detectorType = ''
		self.detectorSize = [0, 0]
		self.fileName = ''
		self.frameAxis = ''
		self.dataType = ''
		self.imageAxis = ''
		self.imageArea = [[0, 0, 0], [0, 0, 0]]
		self.frameArea = [[0, 0], [0, 0]]
		self.frameBins = [0, 0]
		self.timeStamp = 0
		self.imageData = p_array([])

def sifread(file):
	from os import path, SEEK_CUR
	from pylab import array as p_array
	from sys import exit
	import array

	def readLine(file):
		t = ' '
		s = ''
		while len(t) > 0:
			t = file.read(1)
			if (len(t) >= 1) and (ord(t[0]) >= 32):
				s += t[0]
			else:
				t = ''
		return s

	def skipLine():
		if readLine(f) == '':
			f.close()
			error('Inconsistent image header.')
	def error(s):
		print('Error: %s' % s)
		exit()

	def readSection():
		def readString():
			s = readLine(f).strip()
			n = int(s)
			s = f.read(n)
			if ((n > 0) and (s == '')) or (n < 0):
				f.close()
				error('Inconsistent string.')
			return s

		def tofloat(o):
			for i in range(len(o)):
				o[i] = float(o[i])
			return o

		def toint(o):
			for i in range(len(o)):
				o[i] = int(o[i])
			return o

		def skipandread():
			s = ''
			while (s == ''):
				s = readLine(f).strip()
			return s

		image = SIFimage()
		o = skipandread().split()
		image.temperature = int(o[5])
		o = tofloat(skipandread().split())
		[image.exposureTime, image.cycleTime, image.accumulateCycleTime, image.accumulateCycles] = o[1:5]
		o = tofloat(skipandread().split())
		[image.stackCycleTime, image.pixelReadoutTime] = o[1:3]
		o = skipandread().split()
		image.gainDAC = float(o[2])
		o = skipandread().split()
		image.detectorType = o[0]
		o = toint(skipandread().split())
		image.detectorSize = o[0:2]
		o = skipandread().split()
		image.fileName = o[0]
		for n in range(3):
			o = skipandread()
		o = toint(skipandread().split())
		image.shutterTime = o[4:6]
		for n in range(15):
			o = skipandread()
		image.frameAxis = readString()
		image.dataType = readString()
		image.imageAxis = readString()
		o = skipandread().split()
		o += skipandread().split()
		o = toint(o)
		image.imageArea = [[o[1], o[4], o[6]], [o[3], o[2], o[5]]]
		image.frameArea=[[o[10], o[13]], [o[12], o[11]]]
		image.frameBins=[o[15], o[14]]
		s = int(((1 - (image.frameArea[0][0] - image.frameArea[1][0]))/(1.*image.frameBins[0]))*((1 - (image.frameArea[0][1] - image.frameArea[1][1]))/(1.*image.frameBins[1])))
		z = 1 + (image.imageArea[0][2] - image.imageArea[1][2])
		if (s != o[8]) or (o[8]*z != o[7]):
			f.close()
			error('Inconsistent image header.')
		for n in range(z):
			o = readString()
		o = array.array('i')
		o.fromfile(f, 1)
		image.timeStamp = o.tolist()[0]
		f.seek(-4, SEEK_CUR)
		o = array.array('f')
		o.fromfile(f, s*z)
		image.imageData = p_array(o.tolist()).reshape(image.frameArea[1][0], image.frameArea[1][1], z)
		readString()
		o = skipandread().split()
		next = int(o[0])
		return [image, next]

	if not path.exists(file):
		error('File (%s) does not exist.' % file)

	f = open(file, 'rb')
	if f < 0:
		error('Could not open the file.')
	if not (readLine(f) == 'Andor Technology Multi-Channel File'):
		f.close()
		error('Not an Andor SIF image file.')
	skipLine()
	[data,next] = readSection()
	data.seqNum = 1
	if (next == 1):
		[back,next] = readSection()
		back.seqNum = 2
		if (next == 1):
			ref = copy(back)
			ref.seqNum = 3
			back = readSection()
			back.seqNum = 2
		else:
			ref = SIFimage()
	else:
		back = SIFimage()
		ref = copy(back)
	f.close()

	return [data, back, ref]
