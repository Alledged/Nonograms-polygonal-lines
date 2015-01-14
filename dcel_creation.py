# this script creates a dcel using an input file passed as argument

import DCEL
import Point
import Rational

import types
from sys import maxint




# ---------------------------

def parse_file_and_bounding_box(file_name):
	""" Parse the coordinates file. Works with ints and Rationals. 
	
	It returns a list of edges, where one edge is defined by one line
	using its start and end point.

	Also calculates good dimensions for the bounding box (not 
	necessarily a square box), using the coordinates read and
	the SIDE constant
	"""

	bbox_x_top = ()
	bbox_x_bot = ()
	bbox_y_left = ()
	bbox_y_right = ()

	bounding_box = []

	SIDE = 10

	# max and min values used to compare with actual coordinates 
	# to find good dimensions for the bounding box
	bounding = [maxint, -(maxint-1), maxint, -(maxint-1)]
	edges = []
	for line in file(file_name):
		data = line.split()
		for i in range(len(data)):

			# checking if the coordinate read is an int or in 
			# Rational form (with a '/')
			if('/' in data[i]):
				m = re.search('(-*\d+)/(-*\d+)', data[i])
				data[i] = Rational.Rational(int(m.group(1)), int(m.group(2)))
			else:
				data[i] = int(data[i])

		# updating the min_x, max_x, min_y, max_y using the 
		# current line of four coordinates
		if(data[0] < bounding[0]):
			bounding[0] = data[0]
		if(data[0] > bounding[1]):
			bounding[1] = data[0]
		if(data[1] < bounding[2]):
			bounding[2] = data[1]
		if(data[1] > bounding[3]):
			bounding[3] = data[1]

		# appending newly created 2D tuple of Point.Point s
		# to variable "edges" which must be returned		
		edges.append((Point.Point(data[0], data[1]),
			Point.Point(data[2], data[3])))

	# using global variables bbox_x/y_top/bot/left/right to 
	# update the empty tuple with the extreme points found 
	# previously and the constant SIDE
	#global bbox_x_top 
	bbox_x_top += (Point.Point(bounding[0]-SIDE, bounding[3]+SIDE), 
		Point.Point(bounding[1]+SIDE, bounding[3]+SIDE),)

	#global bbox_x_bot 
	bbox_x_bot += (Point.Point(bounding[0]-SIDE, bounding[2]-SIDE),
		Point.Point(bounding[1]+SIDE, bounding[2]-SIDE),)

	#global bbox_y_left 
	bbox_y_left += (Point.Point(bounding[0]-SIDE, bounding[3]+SIDE),
		Point.Point(bounding[0]-SIDE, bounding[2]-SIDE),)

	#global bbox_y_right 
	bbox_y_right += (Point.Point(bounding[1]+SIDE, bounding[3]+SIDE),
		Point.Point(bounding[1]+SIDE, bounding[2]-SIDE),)

	bounding_box.append(bbox_x_top)
	bounding_box.append(bbox_x_bot)
	bounding_box.append(bbox_y_left)
	bounding_box.append(bbox_y_right)

	return edges, bounding_box


# def parse_file(file_name):
# 	"""Returns a list of 2D tuples of Point.Point, each representing
# 	a edge, the file MUST be in the format "{0} {1} {2} {3}" """
# 	edges = []
# 	for line in file(file_name):
# 		data = line.split()
# 		for i in range(len(data)):

# 			# checking if the coordinate read is an int or in 
# 			# Rational form (with a '/')
# 			if('/' in data[i]):
# 				m = re.search('(-*\d+)/(-*\d+)', data[i])
# 				data[i] = Rational.Rational(int(m.group(1)), int(m.group(2)))
# 			else:
# 				data[i] = int(data[i])

# 		# appending newly created 2D tuple of Point.Point s
# 		# to variable "edges" which must be returned		
# 		edges.append((Point.Point(data[0], data[1]),
# 			Point.Point(data[2], data[3])))
		
# 	return edges

def create_dcel(edges, pts=[]):
	dcel = DCEL.buildGeneralSubdivision(edges, pts)
	return dcel

