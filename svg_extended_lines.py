# script combining extending the lines of the original
# drawing and drawing them to an svg file.

import intersections_experiments as ie
import svgwrite
import Point

INPUTFILE = "input_files/fat_tangramcat.txt" 


# I can access the bbox_x_top, bbox_x_bot, 
# bbox_y_left and bbox_y_right

edges = ie.parse_file(INPUTFILE)
all_inter = ie.get_all_legit_intersections(edges)

print all_inter


# create a new drawing function, as the one in draw_dcel
# draws polygons and i want to draw lines.
def draw_extended_lines_svg(list_inters_points, outputfile):
	"""draws the extended edges to the outputfile.svg"""
	dwg = svgwrite.Drawing(filename=outputfile, debug=True)
	
	for pts in list_inters_points:
		print type(pts[0][0])
		# line = svgwrite.shapes.Line(start=(legit[0][0], legit[0][1]), end=(legit[1][0], legit[1][1]))
		# print line
		dwg.add(dwg.line((int(pts[0][0]), int(pts[0][1])), (int(pts[1][0]), int(pts[1][1])), stroke='black'))
	
	dwg.save()


draw_extended_lines_svg(all_inter, 'output.svg')