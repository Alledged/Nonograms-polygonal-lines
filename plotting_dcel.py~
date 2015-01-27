# this script plots points and stores the object in the DCEL
import DCEL
import Point
from operator import methodcaller
import matplotlib.pyplot as plt


# list of 2D tuples of DCEL.Vertex points
BOUNDING_X = [-200, 200, 200, -200, -200]
BOUNDING_Y = [200, 200, -200, -200, 200]

# does not work with page59.txt
FILENAME = "point_files/points_plane.txt"

# unused method
# def read_file(file_name):
# 	"""reads a file and sets points into a list of list"""
# 	lst_points = []
# 	f = open(file_name, "r")
# 	for point in f:
# 		point = point.strip()
# 		point = " ".join(point.split()).split()
# 		point = map(float, point)
# 		lst_points.append(point)
# 	return lst_points


# unused method
# def make_points(file_name):
# 	"""converts a list containing lists of coordinates into a list of Points"""
# 	l_points = read_file(file_name)
# 	proper_points = []
# 	for point in l_points:
# 		proper_points.append(Point.Point(point))
# 	return proper_points
	


# method borrowed from driver.
def parse_file(file_name):
	pts = []
	edges = []
	for line in file(file_name):
		data = line.split()
		if len(data) == 2:
			try:
				pts.append(Point.Point(int(data[0]), int(data[1])))
			except ValueError:
				print "ignoring line:", line
		elif len(data) == 4:
			try:
				# 4 points in file means edge
				edges.append((Point.Point(int(data[0]), int(data[1])),
					Point.Point(int(data[2]), int(data[3]))))
			except ValueError:
				print "ingnoring line:", line

	if edges:
		return DCEL.buildGeneralSubdivision(edges, pts)
	elif pts:
		return DCEL.buildSimplePolygon(pts)


# def calculate_area(face):
# 	area = -1
# 	bounding_vertices_x = []
# 	bounding_vertices_y = []

# 	# identify all points bounding the face in counterclockwise order
# 	# and store their x and y coordinates in two lists
# 	edges = face.getOuterBoundary()
# 	for edge in edges:
# 		bounding_vertices_x.append(edge.getOrigin().getCoords()[0])
# 		bounding_vertices_y.append(edge.getOrigin().getCoords()[1])


	
# 	part_p, part_m = 0, 0
# 	for i_p, i_m in zip(range(len(bounding_vertices_x)), range(len(bounding_vertices_y))):
# 		if i_p == len(bounding_vertices_x) - 1:
# 			part_p += bounding_vertices_x[i_p]*bounding_vertices_y[0]
# 		else:
# 			part_p += bounding_vertices_x[i_p]*bounding_vertices_y[i_p+1]

# 		if i_m == len(bounding_vertices_y) - 1:
# 			part_m += bounding_vertices_x[0]*bounding_vertices_y[i_m]
# 		else:
# 			part_m += bounding_vertices_x[i_m + 1]*bounding_vertices_y[i_m]

	
# 	total = 0.5 * (part_p - part_m)
# 	return total


def main():

	dcel_new = parse_file(FILENAME)
	#dcel_new.plot_whole_dcel()
	#faces = dcel_new.getFaces()
	dcel_new.plot_whole_dcel()
	#faces = dcel_new.getFaces()
	#faces[1].plot_face()
	

if __name__ == '__main__':
	main()