# this script read holes.txt and creates a dcel to investigate how
# holes behave
import DCEL
import Point



def get_data():
	"""reads the data from holes.txt and returns it as a list of list
	of Points.Points (coordinates)"""

	all_loops = []

	f = file("input_files/separated_faces.txt", "r")
	for line in f:
		data = line.split()

		e = (Point.Point(int(data[0]), int(data[1])), Point.Point(int(data[2]), int(data[3]))) 
		all_loops.append(e)

	return all_loops




# flatten the list.
#print [item for sublist in loops for item in sublist]

def convert_to_edges(all_loops):
	"""returns a set of edges for all three loops"""
	all_edges = []
	counter_loop = -1
	for loop in all_loops:
		all_edges.append([])
		counter_loop += 1
		for i in range(len(loop)):
			edge = ()
			if i == len(loop) - 1 :
				# last edge, between last point and first point
				edge += (loop[i], loop[0])
			else:
				edge += (loop[i], loop[i+1])
			all_edges[counter_loop].append(edge)
	return all_edges

# list of list of edges.
#all_edges = convert_to_edges(loops)

# flatten the list to try
#all_edges = [item for sublist in all_edges for item in sublist]
dcel = DCEL.buildGeneralSubdivision(get_data())


# recursive function!
def part_of_drawing(face, value):
	face.set_is_part_of_drawing(value)
	#print face.getOuterBoundary()
	#print "\n"
	#print "assigned once"
	if value == True:
		value = False
	else:
		value = True

	for inner_face_edge in face.getInnerComponents():
		if(inner_face_edge != []):
			part_of_drawing(inner_face_edge.getTwin().getFace(), value)
		
		

val = False
part_of_drawing(dcel.getFaces()[0], val)

for face in dcel.getFaces():
	print face.getOuterBoundary()
	print face.get_is_part_of_drawing()
	print "\n"
