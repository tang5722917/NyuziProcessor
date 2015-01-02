#!/usr/bin/env python
# 
# Copyright (C) 2011-2015 Jeff Bush
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
# 
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301, USA.
# 


#
# Read a Wavefront .OBJ file and convert it into a flat file that can be read
# by the viewer program
#

import sys
import os
import re
import subprocess
import struct

# This is the final output of the parsing stage
textureList = []	# (width, height, data)
meshList = []		# (texture index, vertex list, index list)

materialNameToTextureIdx = {}

size_re = re.compile('Geometry: (?P<width>\d+)x(?P<height>\d+)')
def read_texture(fname):
	width = None
	height = None
	p = subprocess.Popen(['convert', '-debug', 'all', fname, 'rgba:_texture.bin'], stdout=subprocess.PIPE,
		stderr = subprocess.PIPE)
	out, err = p.communicate()
	for line in err.split('\n'):
		got = size_re.search(line)
		if got:
			width = int(got.group('width'))
			height = int(got.group('height'))
			
	with open('_texture.bin', 'rb') as f:
		textureData = f.read()
		
	print 'read texture', fname, width, height, len(textureData)
	return (width, height, textureData)

def read_mtl_file(filename):
	global textureList, materialNameToTextureIdx
	
	currentName = ''
	currentFile = ''
	with open(filename) as f:
		for line in f:
			if line[0] == '#' or line.strip() == '':
				continue
			
			fields = [s for s in line.strip().split(' ') if s]
			if fields[0] == 'newmtl':
				materialNameToTextureIdx[fields[1]] = len(textureList)
				textureList += [ (None, None, None) ]
			elif fields[0] == 'map_Ka':
				textureList[-1] = read_texture(os.path.dirname(filename) + '/' + fields[1])

def read_obj_file(filename):
	global meshList
	
	vertexPositions = []
	textureCoordinates = []
	combinedVertices = []
	vertexToIndex = {}
	triangleIndexList = []
	currentMaterial = None
	meshList = []
	currentTextureId = -1

	with open(filename, 'r') as f:
		for line in f:
			if line[0] == '#' or line.strip() == '':
				continue
			
			fields = [s for s in line.strip().split(' ') if s]
			if fields[0] == 'v':
				vertexPositions += [ (float(fields[1]), float(fields[2]), float(fields[3])) ]
			elif fields[0] == 'vt':
				textureCoordinates += [ (float(fields[1]), float(fields[2])) ]
			elif fields[0] == 'f':
				# The OBJ file references vertexPositions and texture coordinates independently.
				# They must be paired in our implementation. Build a new vertex list that
				# combines those and generate an index list into that.
				polygonIndices = []
				for indexPair in fields[1:]:
					vi, vti = indexPair.split('/')
					vertexAttrs = vertexPositions[int(vi) - 1] + textureCoordinates[int(vti) - 1]
					if vertexAttrs not in vertexToIndex:
						vertexToIndex[vertexAttrs] = len(combinedVertices)
						combinedVertices += [ vertexAttrs ]
				
					polygonIndices += [ vertexToIndex[vertexAttrs] ]

				# faceList is made up of polygons. Convert to triangles
				for index in range(1, len(polygonIndices) - 1):
					triangleIndexList += [ polygonIndices[0], polygonIndices[index], polygonIndices[index + 1] ]
			elif fields[0] == 'g' and triangleIndexList != []:
				# New object, emit the last one and clear the current combined list
				meshList += [ (currentTextureId, combinedVertices, triangleIndexList) ]
				combinedVertices = []
				vertexToIndex = {}
				triangleIndexList = []
			elif fields[0] == 'usemtl':
				currentTextureId = materialNameToTextureIdx[fields[1]]
			elif fields[0] == 'mtllib':
				read_mtl_file(os.path.dirname(filename) + '/' + fields[1])

		if triangleIndexList != []:
			meshList += [ (currentTextureId, combinedVertices, triangleIndexList) ]

def align(addr, alignment):
	return int((addr + alignment - 1) / alignment) * alignment

def write_resource_file(fname):
	global textureList
	global meshList
	
	currentDataOffset = len(textureList) * 8 + len(meshList) * 16 # Skip header
	currentHeaderOffset = 12

	with open(fname, 'wb') as f:
		# Write textures
		for width, height, data in textureList:
			if data == None:
				f.seek(currentHeaderOffset)
				f.write(struct.pack('IHH', 0xffffffff, 0, 0))
				currentHeaderOffset += 8
			else:
				# Write file header
				f.seek(currentHeaderOffset)
				f.write(struct.pack('IHH', currentDataOffset, width, height))
				currentHeaderOffset += 8

				# Write data
				f.seek(currentDataOffset)
				f.write(data)
				currentDataOffset = align(currentDataOffset + len(data), 4)
			
		# Write meshes
		for textureIdx, vertices, indices in meshList:
			currentDataOffset = align(currentDataOffset, 4)

			# Write file header
			f.seek(currentHeaderOffset)
			f.write(struct.pack('IIII', currentDataOffset, textureIdx, len(vertices), len(indices)))
			currentHeaderOffset += 16

			# Write data
			f.seek(currentDataOffset)
			for vert in vertices:
				for val in vert:
					f.write(struct.pack('f', val))
					currentDataOffset += 4
				
			for index in indices:
				f.write(struct.pack('I', index))
				currentDataOffset += 4

		# Write file header
		f.seek(0)
		f.write(struct.pack('I', currentDataOffset)) # total size
		f.write(struct.pack('I', len(textureList))) # num textures
		f.write(struct.pack('I', len(meshList))) # num meshes
		
		print 'wrote', fname

# Main
if len(sys.argv) < 2:
	print 'enter the name of a .OBJ file'
	sys.exit(1)

read_obj_file(sys.argv[1])
write_resource_file('resource.bin')



	





