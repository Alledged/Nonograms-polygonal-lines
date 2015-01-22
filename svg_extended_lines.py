# script combining extending the lines of the original
# drawing and drawing them to an svg file.

import intersections_experiments as ie
import svgwrite
import Point
import re

INPUTFILE = "input_files/fat_tangramcat.txt" 
title = re.match('.+/(.+).txt', INPUTFILE).group(1)

# I can access the bbox_x_top, bbox_x_bot, 
# bbox_y_left and bbox_y_right

edges = ie.parse_file(INPUTFILE)
all_inter = ie.get_all_legit_intersections(edges)

# print all_inter


# create a new drawing function, as the one in draw_dcel
# draws polygons and i want to draw lines.o


# due to the change in coordinate system bbox_x_top is on the bottom and bbox_x_bot is on the top
def draw_extended_lines_svg(list_inters_points, outputfile):
	"""draws the extended edges to the outputfile.svg"""
	dwg = svgwrite.Drawing(filename=outputfile, debug=True)
	
	for pts in list_inters_points:
		dwg.add(dwg.line((int(pts[0][0]), int(pts[0][1])), (int(pts[1][0]), int(pts[1][1])), stroke='black'))


	dwg.add(dwg.line((int(ie.bbox_x_top[0][0]), int(ie.bbox_x_top[0][1])),
		(int(ie.bbox_x_top[1][0]), int(ie.bbox_x_top[1][1])), stroke='black'))	

	dwg.add(dwg.line((int(ie.bbox_x_bot[0][0]), int(ie.bbox_x_bot[0][1])),
		(int(ie.bbox_x_bot[1][0]), int(ie.bbox_x_bot[1][1])), stroke='black'))

	dwg.add(dwg.line((int(ie.bbox_y_left[0][0]), int(ie.bbox_y_left[0][1])),
		(int(ie.bbox_y_left[1][0]), int(ie.bbox_y_left[1][1])), stroke='black'))

	dwg.add(dwg.line((int(ie.bbox_y_right[0][0]), int(ie.bbox_y_right[0][1])),
		(int(ie.bbox_y_right[1][0]), int(ie.bbox_y_right[1][1])), stroke='black'))
	
	# add the title of the drawing
	dwg.add(dwg.text(title, insert=(int(ie.bbox_x_top[0][0]), int(ie.bbox_x_top[0][1])+50)))
	dwg.save()


draw_extended_lines_svg(all_inter, 'output.svg')