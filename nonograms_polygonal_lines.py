# this is the main script

import os
import re
import cPickle
import geomutil
import DCEL
import Point
import Rational


import matplotlib.pyplot as plt
import types
from sys import maxint


FILENAME = "input_files/fat_tamgramcat.txt"
	
SIDE = 10


# really do not like this method, could be placed in parse_file!, but problem when 
# the dcel objects are already in cpickle files (else part of the main if)
def generate_bounding_box():
	""" generates a good dimension bounding box"""
	bounding = [maxint, -(maxint-1), maxint, -(maxint-1)]
	for line in file(FILENAME, 'r'):
		data = line.split()

		for i in range(len(data)):

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


	bbox_x_top = (Point.Point(bounding[0]-SIDE, bounding[3]+SIDE), 
		Point.Point(bounding[1]+SIDE, bounding[3]+SIDE),)

	 
	bbox_x_bot = (Point.Point(bounding[0]-SIDE, bounding[2]-SIDE),
		Point.Point(bounding[1]+SIDE, bounding[2]-SIDE),)

	
	bbox_y_left = (Point.Point(bounding[0]-SIDE, bounding[3]+SIDE),
		Point.Point(bounding[0]-SIDE, bounding[2]-SIDE),)

	
	bbox_y_right = (Point.Point(bounding[1]+SIDE, bounding[3]+SIDE),
		Point.Point(bounding[1]+SIDE, bounding[2]-SIDE),)


	return bbox_x_top, bbox_x_bot, bbox_y_left, bbox_y_right


def parse_file(file_name):
	""" Parse the coordinates file. Works with ints and Rationals. 
	
	It returns a list of edges, where one edge is defined by one line
	using its start and end point.
	"""
	# max and min values used to compare with actual coordinates 
	# to find good dimensions for the bounding box
	
	edges = []
	for line in file(file_name, 'r'):
		data = line.split()
		for i in range(len(data)):

			# checking if the coordinate read is an int or in 
			# Rational form (with a '/')
			if('/' in data[i]):
				m = re.search('(-*\d+)/(-*\d+)', data[i])
				data[i] = Rational.Rational(int(m.group(1)), int(m.group(2)))
			else:
				data[i] = int(data[i])

		# appending newly created 2D tuple of Point.Point s
		# to variable "edges" which must be returned		
		edges.append((Point.Point(data[0], data[1]),
			Point.Point(data[2], data[3])))
	
	return edges


def plot_whole_structure(edges):
	"""This function plots all the faces from the faces only"""
	#print len(edges)
	plt.axis([0,10, 0, 20])
	for edge in edges:
		#lst = face.get_ordered_vertices()
		#if(lst != None):
		plt.plot(
			[edge.getOrigin().getCoords()[0], edge.getDest().getCoords()[0]],
			[edge.getOrigin().getCoords()[1], edge.getDest().getCoords()[1]], color = "blue") # colour if needed
	plt.show()


def legit_intersections(edge, bbox_x_top, bbox_x_bot, bbox_y_left, bbox_y_right):
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
	inters_x_t = geomutil.intersection(edge.getOrigin(), edge.getDest(), bbox_x_top[0], bbox_x_top[1])
	inters_x_b = geomutil.intersection(edge.getOrigin(), edge.getDest(), bbox_x_bot[0], bbox_x_bot[1])
	inters_y_l = geomutil.intersection(edge.getOrigin(), edge.getDest(), bbox_y_left[0], bbox_y_left[1])
	inters_y_r = geomutil.intersection(edge.getOrigin(), edge.getDest(), bbox_y_right[0], bbox_y_right[1])	

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


def plot_extended_edges(edges, b_x_t, b_x_b, b_y_l, b_y_r):
	"""plots the extended edges using the intersection coordinates with
	the bounding box"""
	for edge in edges:
		legit_inters = legit_intersections(edge, b_x_t, b_x_b, b_y_l, b_y_r)
		if(legit_inters != []):
			# plot ([x_1, x_2], [y_1, y_2]), x and y components of the two 
			# intersection points
			plt.plot([legit_inters[0][0], legit_inters[1][0]],
				[legit_inters[0][1], legit_inters[1][1]])

	# show the plot once all edges are drawn
	plt.show()


def create_dcel(edges, pts=[]):
	dcel = DCEL.buildGeneralSubdivision(edges, pts)
	return dcel


def main():

	# check if the dcel parts exits
	# notation -> (type (vertices, edges, face))_(file_name).save 
					# -> pickled file for the type of file_name 

	core_file_name = re.match('.+/(.+).txt', FILENAME).group(1)
	file_name_vertices = 'cpickle/' + core_file_name + '_vertices.save'
	file_name_edges = 'cpickle/' + core_file_name + '_edges.save'
	file_name_faces = 'cpickle/' + core_file_name + '_faces.save'

	# defining empty lists for the vertices, edges, and faces
	vertices = []
	edges = []
	faces = []

	# check if the files does not exists
	if (not os.path.isfile(file_name_vertices)):

		print "CREATION OF DCEL"

		# call to the dcel_generation file
		e = parse_file(FILENAME)

		bbox_x_top, bbox_x_bot, bbox_y_left, bbox_y_right = generate_bounding_box()

		print bbox_x_top, bbox_x_bot, bbox_y_left, bbox_y_right

		dcel = create_dcel(e)


		# assignment to the aforementioned variables
		vertices = dcel.getVertices()
		edges = dcel.getEdges()
		faces = dcel.getFaces()


		# MAYBE DELETE dcel?

		# pickling for the next use
		#---------------
		# MAYBE CAN PICKLE THE THREE AT THE SAME TIME! CHECK
		#---------------
		f_v = file(file_name_vertices, 'wb')
		cPickle.dump(vertices, f_v, protocol = cPickle.HIGHEST_PROTOCOL)
		f_v.close()

		f_e = file(file_name_edges, 'wb')
		cPickle.dump(edges, f_e, protocol = cPickle.HIGHEST_PROTOCOL)
		f_e.close()

		f_f = file(file_name_faces, 'wb')
		cPickle.dump(faces, f_f, protocol = cPickle.HIGHEST_PROTOCOL)
		f_f.close()

	else:

		print "ONLY UNPICKLING"

		bbox_x_top, bbox_x_bot, bbox_y_left, bbox_y_right = generate_bounding_box()

		# unpickle the files
		f_v = file(file_name_vertices, 'rb')
		f_e = file(file_name_edges, 'rb')
		f_f = file(file_name_faces, 'rb')


		vertices = cPickle.load(f_v)
		edges = cPickle.load(f_e)
		faces = cPickle.load(f_f)

		f_v.close()
		f_e.close()
		f_f.close()



	#plot_extended_edges(edges, bbox_x_top, bbox_x_bot, bbox_y_left, bbox_y_right)
	plot_whole_structure(edges)


	# should have access to vertices, edges and faces
	


if __name__ == '__main__':
	main()