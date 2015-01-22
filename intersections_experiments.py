# this script prints onto a single figure plots generated in a lookup
import geomutil
import Point
import DCEL
import Rational

import matplotlib.pyplot as plt
import types
import re
from sys import maxint
import cPickle



# file from which the points are read, format -> x_1 y_1 x_2 y_2
FILENAME = "input_files/points_plane.txt"

# buffer # of pixels to add to create the bounding box
SIDE = 100

# ------ BOUNDING BOX -------
# Empty tuples, one for each of the bounding line,
# their appropriate values (depending on the input points),
# will be calculated in the "parse_file" method. They are 
# 2D tuples of Point.Point objects

bbox_x_top = ()
bbox_x_bot = ()
bbox_y_left = ()
bbox_y_right = ()

# ---------------------------



def parse_file(file_name):
	""" Parse the coordinates file. Works with ints and Rationals. 
	
	It returns a list of edges, where one edge is defined by one line
	using its start and end point.

	Also calculates good dimensions for the bounding box (not 
	necessarily a square box), using the coordinates read and
	the SIDE constant
	"""
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
	global bbox_x_top 
	bbox_x_top += (Point.Point(bounding[0]-SIDE, bounding[3]+SIDE), 
		Point.Point(bounding[1]+SIDE, bounding[3]+SIDE),)

	global bbox_x_bot 
	bbox_x_bot += (Point.Point(bounding[0]-SIDE, bounding[2]-SIDE),
		Point.Point(bounding[1]+SIDE, bounding[2]-SIDE),)

	global bbox_y_left 
	bbox_y_left += (Point.Point(bounding[0]-SIDE, bounding[3]+SIDE),
		Point.Point(bounding[0]-SIDE, bounding[2]-SIDE),)

	global bbox_y_right 
	bbox_y_right += (Point.Point(bounding[1]+SIDE, bounding[3]+SIDE),
		Point.Point(bounding[1]+SIDE, bounding[2]-SIDE),)

	# return the list of tuples of Point.Point (list of edges)
	return edges

#THIS METHOD IS ONLY FOR A SINGLE EDGE!!
def legit_intersections(edge):
	"""Returns list of two legitimate intersection points between the
	original edge (unexetended) and the bounding box. 

	One edge can only intersect with two sides of the bounding box 
	(DEGENERACY when intersecting with the corner of the bounding box !!!)
	"""
	# empty list to return
	legit = []


	# using the geomuil module, find the intersection point for each line with the 
	# four edges of the bounding box. Some of those may be undefined if the edge and 
	# that of the bounding box are parallel!, assign then the value None.
	inters_x_t = geomutil.intersection(edge[0], edge[1], bbox_x_top[0], bbox_x_top[1])
	inters_x_b = geomutil.intersection(edge[0], edge[1], bbox_x_bot[0], bbox_x_bot[1])
	inters_y_l = geomutil.intersection(edge[0], edge[1], bbox_y_left[0], bbox_y_left[1])
	inters_y_r = geomutil.intersection(edge[0], edge[1], bbox_y_right[0], bbox_y_right[1])	

	# counter of legitimate intersection used to take care of the corner intersection 
	# degeneracy
	number_inters = 0

	# for the four intersection point, check if its type is not None, then check whether it
	# is in the range of the bounding box. If so append it to legit and increment the counter
	if (not isinstance(inters_x_t, types.NoneType) and inters_x_t[0] >= bbox_x_top[0][0] and inters_x_t[0] <= bbox_x_top[1][0]):
		legit.append(inters_x_t)
		number_inters += 1
	if (not isinstance(inters_x_b, types.NoneType) and inters_x_b[0] >= bbox_x_bot[0][0] and inters_x_b[0] <= bbox_x_bot[1][0]):
		legit.append(inters_x_b)
		number_inters += 1
	if (not isinstance(inters_y_l, types.NoneType) and inters_y_l[1] >= bbox_y_left[1][1]
		and inters_y_l[1] <= bbox_y_left[0][1] and number_inters < 2):
		legit.append(inters_y_l)
		number_inters += 1
	if (not isinstance(inters_y_r, types.NoneType) and inters_y_r[1] >= bbox_y_right[1][1]
		and inters_y_r[1] <= bbox_y_right[0][1] and number_inters < 2):
		legit.append(inters_y_r)
		number_inters += 1

	return legit

def get_all_legit_intersections(edges):
	"""calls the legit intersections for all edge in edges
	and returns a list of list of intersection points"""
	all_intersections = []	
	for edge in edges:
		legit = legit_intersections(edge)
		all_intersections.append(legit)
	return all_intersections

def write_extended_point_to_file(edges):
	"""Uses the same name as the input file with: _extented.txt at the end and 
	for each edge write the intersection coordinate between the edge and the 
	bounding box. If coordinate is a Rational, then the number is printed as 
	such (a/b)"""

	#slicing the FILENAME and appending _extended.txt 
	file_name_extended = FILENAME[:-4:] + "_extended.txt"
	f = open(file_name_extended, "w")

	for edge in edges:
		legit_inters = legit_intersections(edge)
		if(legit_inters != []):
			f.write("{0} {1} {2} {3}\n".format(legit_inters[0][0],
				legit_inters[0][1], legit_inters[1][0], legit_inters[1][1]))

	f.close()

def plot_extended_edges(edges):
	"""plots the extended edges using the intersection coordinates with
	the bounding box"""
	for edge in edges:
		legit_inters = legit_intersections(edge)
		if(legit_inters != []):
			# plot ([x_1, x_2], [y_1, y_2]), x and y components of the two 
			# intersection points
			plt.plot([legit_inters[0][0], legit_inters[1][0]],
				[legit_inters[0][1], legit_inters[1][1]])

	# show the plot once all edges are drawn
	plt.show()
 


def main():
	"""main function where the code is executed"""
	e = parse_file(FILENAME)
	# put the extended edges into a DCEL, without have an extra face for 
	# the bounding box

	# would need a way to save this data structure: ASK PROFESSOR OR D
	# using pickle or so!!
	
	dcel_ = DCEL.buildGeneralSubdivision(e, [])



	print dcel_.getVertices()
	# we want the vertices, edges and faces.
	
	#f_vertices = file('structs/vertices.save', 'wb')
	#cPickle.dump(dcel_extended.getVertices(), f_vertices, protocol = cPickle.HIGHEST_PROTOCOL)
	#f_vertices.close()

	#f_edges = file('structs/edges.save', 'wb')
	#cPickle.dump(dcel_extended.getEdges(), f_edges, protocol=cPickle.HIGHEST_PROTOCOL)
	#f_edges.close()

	#f_faces = file('structs/faces.save', 'wb')
	#cPickle.dump(dcel_extended.getFaces(), f_faces, protocol=cPickle.HIGHEST_PROTOCOL)
	#f_faces.close()


	#
if __name__ == '__main__':
	main()