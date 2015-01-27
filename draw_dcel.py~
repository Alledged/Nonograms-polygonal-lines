# This script takes care of the svg drawing of the DCEL.
# done in the draw() method.
import DCEL
import svgwrite


def convert_to_points(list_x_y):
	"""from a tuple of lists ([x1,x2,...], [y1,y1,...]) to a list of [(x1,y1), (x2,y2), ...]"""
	pts = []
	for i in range(len(list_x_y[0])):
		pts.append((list_x_y[0][i], list_x_y[1][i]))
	return pts


def draw(faces, output_file):
	"""this function draws all faces to the output file given, those part of the figure
	in black and the others in white"""
	dwg = svgwrite.Drawing(filename=output_file, debug=True)
	for face in faces:
		# vertices is a tuple of list ([x_1,x_2,...], [y_1,y_2,...])
		if(face.get_ordered_vertices() != None):
			vertices = convert_to_points(face.get_ordered_vertices())
			if face.get_is_part_of_drawing() == True:
				# color black
				dwg.add(dwg.polygon(vertices, stroke='black', fill='black'))	
			else:
				# color white
				dwg.add(dwg.polygon(vertices, stroke='black', fill='white'))

	dwg.save()