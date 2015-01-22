# This script read an input file in format {0} {1} {2} {3} and 
# creates a DCEL from it, and assigns to each face whether it
# is part of the original drawing. The entire DCEL can then be
# drawn to a svg file.
import DCEL
import Point
import draw_dcel

FILENAME = "input_files/fat_tangramcat.txt"
OUTPUT_FILE = "output.svg"


#problem with some of the input files, those with negative number, as svg starts at 
# (0,0) at the top left
#MAYBE CONVERT TO COORDINATES TO SOMETHING THAT CAN BE SEEN IN THE BROWSER


def main():
	edges = parse_file(FILENAME)
	dcel = DCEL.buildGeneralSubdivision(edges)
	part_of_drawing(dcel.getFaces()[0], False)

	# draw the DCEL to svg file
	draw_dcel.draw(dcel.getFaces(), OUTPUT_FILE)


def parse_file(filename):
	"""reads the data from holes.txt and returns it as a list of 
	edges, which are 2D tuples of Point.Point instances"""
	edges = []
	try:
		f = file(filename, 'r')
		for line in f:
			data = line.split()
			e = (Point.Point(int(data[0]), int(data[1])), Point.Point(int(data[2]), int(data[3]))) 
			edges.append(e)

	except IndexError:
		print "ERROR!!!, file should have 4 columns"		
	return edges


# recursive function!
def part_of_drawing(face, value):
	"""Sets the variable is_part_of_drawing to each face depending 
	on whether the face is part of the original drawing"""
	face.set_is_part_of_drawing(value)
	if value == True:
		value = False
	else:
		value = True

	for inner_face_edge in face.getInnerComponents():
		if(inner_face_edge != []):
			part_of_drawing(inner_face_edge.getTwin().getFace(), value)
		
def draw_structure(faces, outputfile):
	part_of_drawing(faces[0], False)
	draw_dcel.draw(faces, outputfile)	



if __name__ == '__main__':
	main()
