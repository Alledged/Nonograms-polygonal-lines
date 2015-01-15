# this script read holes.txt and creates a dcel to investigate how
# holes behave
import DCEL
import Point



def get_data():
	"""reads the data from holes.txt and returns it as a list of list
	of Points.Points (coordinates)"""

	all_loops = []

	f = file("input_files/holes.txt", "r")
	current_loop = -1
	for line in f:
		data = line.split()
		# new loop starting
		if len(data) == 1:
			current_loop += 1
			# initialise a new list
			all_loops.append([])
		else:
			p = Point.Point(int(data[0]), int(data[1]))
			all_loops[current_loop].append(p)

	return all_loops


loops = get_data()

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
all_edges = convert_to_edges(loops)

# flatten the list to try
all_edges = [item for sublist in all_edges for item in sublist]

dcel = DCEL.buildGeneralSubdivision(all_edges)
