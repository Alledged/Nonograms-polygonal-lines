# script combining extending the lines of the original
# drawing and drawing them to an svg file.

import intersections_experiments as ie

INPUTFILE = "input_files/fat_tangramcat.txt" 


# I can access the bbox_x_top, bbox_x_bot, 
# bbox_y_left and bbox_y_right

edges = ie.parse_file(INPUTFILE)
all_inter = ie.get_all_legit_intersections(edges)
print len(all_inter)


# create a new drawing function, as the one in draw_dcel
# draws polygons and i want to draw lines.
def draw_extended_lines_svg(edges, outputfile):
	pass