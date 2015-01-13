# this script creates a dcel using an input file passed as argument

import DCEL
import Point
import Rational

def parse_file(file_name):
	"""returns a list of 2D tuples of Point.Point, each representing
	a edge"""
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

		# appending newly created 2D tuple of Point.Point s
		# to variable "edges" which must be returned		
		edges.append((Point.Point(data[0], data[1]),
			Point.Point(data[2], data[3])))

	return edges

def create_dcel(edges, pts=[]):
	dcel = DCEL.buildGeneralSubdivision(edges, pts)
	return dcel