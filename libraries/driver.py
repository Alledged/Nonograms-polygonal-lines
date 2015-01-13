from cs1graphics import *
import DCEL
import Point
import triangulate
import sys


if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'point_files/points_square_half.txt'

def parseRawFile(filename):
    pts = []
    edges = []
    for line in file(filename):
        data = line.split()
        if len(data) == 2:
            try:
                pts.append(Point.Point(int(data[0]),int(data[1])))   # x,y values
            except ValueError:
                print 'ignoring line:',line
        elif len(data) == 4:
            try:
                edges.append((Point.Point(int(data[0]),int(data[1])),
                              Point.Point(int(data[2]),int(data[3]))))
            except ValueError:
                print 'ignoring line:',line
    if edges:
        return DCEL.buildGeneralSubdivision(edges,pts)
    elif pts:
        return DCEL.buildSimplePolygon(pts)
    else:
        return None


dc = parseRawFile(filename)
#dc.validate();  print 'self-consistency of DCEL verified'

print
print 'rendering original subdivision'
layBefore,lookup = DCEL.renderDCEL(dc)
layBefore.move(50,350)
beforeImage = Canvas(500,400)
beforeImage.add(layBefore)

triangulate.triangulate(dc,lookup)
dc.validate();  print 'self-consistency of DCEL verified'

print
print 'rendering subdivision after the triangulation'
layAfter,lookup = DCEL.renderDCEL(dc)
layAfter.move(50,350)
afterImage = Canvas(500,400)
afterImage.add(layAfter)


filenameDot = filename.rfind('.')
if filenameDot != -1:
    filenameBase = filename[:filenameDot]

beforeImage.saveToFile(filenameBase+"Before.ps")
afterImage.saveToFile(filenameBase+"After.ps")
