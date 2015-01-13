# this is the main script
import dcel_creation
import os
import re
import cPickle
import intersections_experiments as ie



FILENAME = "input_files/points_plane.txt"


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
		dcel = dcel_creation.create_dcel(dcel_creation.parse_file(FILENAME))


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


		e = ie.parse_file(FILENAME)



	# should have access to vertices, edges and faces
	


if __name__ == '__main__':
	main()