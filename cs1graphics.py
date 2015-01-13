import copy as _copy
import math as _math
import random as _random
import threading as _threading
import Queue as _Queue
import inspect as _inspect

try:
    set                                # Python 2.4 or later
except:
    try:
        from sets import Set as set    # Python 2.3 compatibility
    except:
        raise RuntimeError('cannot find set class')

_debug = 0    # no debugging
#_debug = 2   # can be 1 or 2 or 3

_ourRandom = _random.Random()
_ourRandom.seed(1234) # initialize the random seed so that treatment of equal depths is reproducible

_underlyingLibrary = None
_graphicsManager = None


class _GraphicsManager(_threading.Thread):
  def __init__(self):
    _threading.Thread.__init__(self)
    self._running = True
    self._referenceCount = 1
    
    # Synchornization mechanisms
    self._commandQueue = _Queue.Queue()
    self._releaseQueue = _Queue.Queue()
    
    # Underlying objects
    self._underlyingObject = dict()     # Key is chain, value is a renderedDrawable
    self._objectChain = tuple()         # Current chain of objects, each item in tuple is pair: (id, callingFunction)
    self._transformChain = tuple()
    self._transforms = dict()
    self._renderOrder = dict()          # For each canvas a list indicating the order everything is rendered
    self._currentCanvas = None
    
    self._needsUpdating = dict()        # Key = canvas, value = set of drawables
    self._needsUpdatingStack = list()
    
    # Event handling
    self._handlers = dict()             # Key = drawable or canvas, value = callback object
    
    # Mouse
    self._mousePrevPosition = None
    self._mouseButtonDown = False
    

  def run(self):
    if _debug >= 2: print "Starting graphics manager"
    self._running = True
    self._periodicCall()

  def stop(self):
    if _debug >= 2: print "Stoping graphics manager"
    self._running = False

  def addCommandToQueue(self, command, blocking=False):
    if self._running:
      self._commandQueue.put( (command, _inspect.stack()[2][2], blocking) )
      if blocking:
        self._releaseQueue.get()

  def processCommands(self):
    while self._running and self._commandQueue.qsize() > 0:
      try:
        (command, caller, blocking) = self._commandQueue.get(0)
        if _debug >= 2:
          print
          print "Manager executing:", command, caller, blocking
        if _debug >= 3:
          print "Current chain:", self._objectChain

        # Canvases
        if command[0] == 'create canvas':
          command[1]._canvas = _RenderedCanvas( command[1], command[2], command[3], command[4], command[5], command[6])
          self._renderOrder[command[1]] = []
          self._needsUpdating[command[1]] = set()

        elif command[0] == 'update canvas':
          command[1]._canvas.setHeight(command[2])
          command[1]._canvas.setWidth(command[3])
          command[1]._canvas.setBackgroundColor(command[4])
          command[1]._canvas.setTitle(command[5])
          
        elif command[0] == 'begin refresh':
          self._objectChain = ((command[1], None), )
          self._transformationChain = (Transformation(), )
          self._currentCanvas = command[1]
          self._renderOrder[command[1]] = list()
          self._needsUpdatingStack = [command[2]]
          
        elif command[0] == 'complete refresh':
          # Remove any deleted objects
          for item in self._underlyingObject.keys():
            if item[0][0] == self._currentCanvas and item not in self._renderOrder[self._currentCanvas]:
              self.removeUnderlying(item)
          
          self._objectChain = tuple()
          self._tranformationChain = tuple()
          self._currentCanvas = None
          
        # Drawables
        elif command[0] == 'begin draw':
          self._objectChain += ( (command[1], caller), )
          if len(self._objectChain) > 2 and self._objectChain[-1][0] == self._objectChain[-2][0]:
            self._transformationChain += (self._transformationChain[-1], )
          else:
            self._transformationChain += (self._transformationChain[-1] * command[1]._transform, )
          _graphicsManager._transforms[self._objectChain] = self._transformationChain[-1]
          self._renderOrder[self._currentCanvas].append(self._objectChain)
          self._needsUpdatingStack.append( self._needsUpdatingStack[-1] or (command[1] in self._needsUpdating[self._currentCanvas]) )
          if not self._underlyingObject.has_key(self._objectChain):
            self._needsUpdatingStack[-1] = True
          
        elif command[0] == 'complete draw':
          self._objectChain = self._objectChain[:-1]
          self._transformationChain = self._transformationChain[:-1]
          last = self._needsUpdatingStack.pop()
          if last and len(self._needsUpdatingStack) > 0:
            self._needsUpdatingStack[-1] = True
          self._needsUpdating[self._currentCanvas].discard(command[1])
          
        elif command[0] == 'draw circle':
          chain = self._objectChain
          if self._underlyingObject.has_key(chain):
            if self._needsUpdatingStack[-1]:
              # If it exists update it
              self._underlyingObject[chain].update(self._transformationChain[-1])
          else:
              # Create object
              self._underlyingObject[chain] = _RenderedCircle( command[1], self._currentCanvas, self._transformationChain[-1] )
            
        elif command[0] == 'draw rectangle':
          chain = self._objectChain
          if self._underlyingObject.has_key(chain):
            if self._needsUpdatingStack[-1]:
              # If it exists update it
              self._underlyingObject[chain].update(self._transformationChain[-1])
          else:
            # Create object
            self._underlyingObject[chain] = _RenderedRectangle( command[1], self._currentCanvas, self._transformationChain[-1] )
            
        elif command[0] == 'draw path':
          chain = self._objectChain
          if self._underlyingObject.has_key(chain):
            if self._needsUpdatingStack[-1]:
              # Update the circle cordinates and size
              self._underlyingObject[chain].update(self._transformationChain[-1])
          else:
            # Create circle in the correct position and add it to the canvas
            self._underlyingObject[self.getCurrentChain()] = _RenderedPath( command[1], self._currentCanvas, self._transformationChain[-1], command[1].getPoints() )
            
        elif command[0] == 'draw polygon':
          chain = self._objectChain
          if self._underlyingObject.has_key(chain):
            if self._needsUpdatingStack[-1]:
              # Update the circle cordinates and size
              self._underlyingObject[chain].update(self._transformationChain[-1])
          else:
            # Create circle in the correct position and add it to the canvas
            self._underlyingObject[self.getCurrentChain()] = _RenderedPolygon( command[1], self._currentCanvas, self._transformationChain[-1], command[1].getPoints() )

        elif command[0] == 'draw text':
          chain = self._objectChain
          if self._underlyingObject.has_key(chain):
            if self._needsUpdatingStack[-1]:
              self._underlyingObject[chain].update(self._transformationChain[-1])
          else:
            self._underlyingObject[self.getCurrentChain()] = _RenderedText( command[1], self._currentCanvas, self._transformationChain[-1] )

            
            
        if blocking:
          if _debug >= 2:
            print "Releasing queue"
          self._releaseQueue.put(None)
      except _Queue.Empty:
        pass

  def getCurrentTransform(self):
    return self._statusStack[-1][0]

  def getCurrentCanvas(self):
    return self._objectChain[0][0]

  def getCurrentChain(self):
    return self._objectChain

  def objectChanged(self, drawable):
    for can in self._renderOrder.keys():
      self._needsUpdating[can].add(drawable)
      if can._autoRefresh:
        can.refresh()

  def removeUnderlying(self, chain):
    pass

  def addHandler(self, shape, callback):
    if self._handlers.has_key(shape):
      self._handlers[shape].append(callback)
    else:
      self._handlers[shape] = [callback]

  def removeHandler(self, shape, callback):
    self._handlers[shape].remove(callback)

  def triggerHandler(self, shape, event):
    if self._handlers.has_key(shape):
      for handler in self._handlers[shape]:
        handler.handle(event)
      return True
    return False

class Point(object):
  """
  Stores a two-dimensional point using cartesian coordinates.
  """
  
  def __init__(self, initialX=0, initialY=0):
    """
    Create a new point instance.

    initialX   x-coordinate of the point (defaults to 0)
    initialY   y-coordinate of the point (defaults to 0)
    """
    if not isinstance(initialX, (int,float)):
      raise TypeError, 'numeric value expected for x-coodinate'

    if not isinstance(initialY, (int,float)):
      raise TypeError, 'numeric value expected for y-coodinate'

    self._x = initialX
    self._y = initialY

  def getX(self):
    """
    Returns the x-coordinate.
    """
    return self._x

  def setX(self, val):
    """
    Set the x-coordinate to val.
    """
    self._x = val

  def getY(self):
    """
    Returns the y-coordinate.
    """
    return self._y

  def setY(self, val):
    """
    Set the y-coordinate to val.
    """
    self._y = val

  def get(self):
    """
    Returns an (x,y) tuple.
    """
    return self._x, self._y

  def scale(self, factor):
    self._x *= factor
    self._y *= factor
    
  def distance(self, other):
    dx = self._x - other._x
    dy = self._y - other._y
    return _math.sqrt(dx * dx + dy * dy)

  def normalize(self):
    mag = self.distance( Point() )
    if mag > 0:
      self.scale(1/mag)

  def __str__(self):
    return '<' + str(self._x) + ',' + str(self._y) + '>'

  def __add__(self, other):
    return Point(self._x + other._x, self._y + other._y)

  def __mul__(self, operand):
    if isinstance(operand, (int,float)):         # multiply by constant
      return Point(self._x * operand, self._y * operand)
    elif isinstance(operand, Point):           # dot-product
      return self._x * operand._x + self._y * operand._y

  def __rmul__(self, operand):
    return self * operand

  def __xor__(self, angle):
    """
    Returns a new point instance representing the original, rotated about the origin.

    angle  number of degrees of rotation (clockwise)
    """
    angle = -_math.pi*angle/180.
    mag = _math.sqrt(self._x * self._x + self._y * self._y)
    return Point(self._x * _math.cos(angle) - self._y * _math.sin(angle), self._x * _math.sin(angle) + self._y * _math.cos(angle))

class Transformation(object):
  def __init__(self, value=None):
    if value:
      self._matrix = value[:4]
      self._translation = value[4:]
    else:
      self._matrix = (1.,0.,0.,1.)
      self._translation = (0.,0.)

  def __repr__(self):
    return '\n   Transformation '+str(hex(id(self)))+':\n   matrix = %s\n   translation = %s\n'%(repr(self._matrix),
                                         repr(self._translation))
    
  def image(self, point):
    return Point( self._matrix[0]*point._x + self._matrix[1]*point._y + self._translation[0],
      self._matrix[2]*point._x + self._matrix[3]*point._y + self._translation[1])

  def inv(self):
    detinv = 1. / self.det()
    m = ( self._matrix[3] * detinv, -self._matrix[1] * detinv, -self._matrix[2] * detinv, self._matrix[0] * detinv )
    t = ( -m[0]*self._translation[0] - m[1]*self._translation[1], -m[2]*self._translation[0] - m[3]*self._translation[1])

    return Transformation(m+t)

  def __mul__(self, other):
    m = ( self._matrix[0] * other._matrix[0] + self._matrix[1] * other._matrix[2],
      self._matrix[0] * other._matrix[1] + self._matrix[1] * other._matrix[3],
      self._matrix[2] * other._matrix[0] + self._matrix[3] * other._matrix[2],
      self._matrix[2] * other._matrix[1] + self._matrix[3] * other._matrix[3])

    p = self.image( Point(other._translation[0], other._translation[1]) )

    return Transformation(m + (p.getX(), p.getY()))

  def det(self):
    return (self._matrix[0] * self._matrix[3] - self._matrix[1] * self._matrix[2])

class Color(object):
  """
  Represents a color.

  Color can be specified by name or RGB value, and can be made transparent.
  """
  _colorValues = {
    'aliceblue'            : (240,248,255), 'antiquewhite'         : (250,235,215), 'antiquewhite1'        : (255,239,219),
    'antiquewhite2'        : (238,223,204), 'antiquewhite3'        : (205,192,176), 'antiquewhite4'        : (139,131,120),
    'aquamarine'           : (127,255,212), 'aquamarine1'          : (127,255,212), 'aquamarine2'          : (118,238,198),
    'aquamarine3'          : (102,205,170), 'aquamarine4'          : ( 69,139,116), 'azure'                : (240,255,255),
    'azure1'               : (240,255,255), 'azure2'               : (224,238,238), 'azure3'               : (193,205,205),
    'azure4'               : (131,139,139), 'beige'                : (245,245,220), 'bisque'               : (255,228,196),
    'bisque1'              : (255,228,196), 'bisque2'              : (238,213,183), 'bisque3'              : (205,183,158),
    'bisque4'              : (139,125,107), 'black'                : (  0,  0,  0), 'blanchedalmond'       : (255,235,205),
    'blue'                 : (  0,  0,255), 'blue1'                : (  0,  0,255), 'blue2'                : (  0,  0,238),
    'blue3'                : (  0,  0,205), 'blue4'                : (  0,  0,139), 'blueviolet'           : (138, 43,226),
    'brown'                : (165, 42, 42), 'brown1'               : (255, 64, 64), 'brown2'               : (238, 59, 59),
    'brown3'               : (205, 51, 51), 'brown4'               : (139, 35, 35), 'burlywood'            : (222,184,135),
    'burlywood1'           : (255,211,155), 'burlywood2'           : (238,197,145), 'burlywood3'           : (205,170,125),
    'burlywood4'           : (139,115, 85), 'cadetblue'            : ( 95,158,160), 'cadetblue1'           : (152,245,255),
    'cadetblue2'           : (142,229,238), 'cadetblue3'           : (122,197,205), 'cadetblue4'           : ( 83,134,139),
    'chartreuse'           : (127,255,  0), 'chartreuse1'          : (127,255,  0), 'chartreuse2'          : (118,238,  0),
    'chartreuse3'          : (102,205,  0), 'chartreuse4'          : ( 69,139,  0), 'chocolate'            : (210,105, 30),
    'chocolate1'           : (255,127, 36), 'chocolate2'           : (238,118, 33), 'chocolate3'           : (205,102, 29),
    'chocolate4'           : (139, 69, 19), 'coral'                : (255,127, 80), 'coral1'               : (255,114, 86),
    'coral2'               : (238,106, 80), 'coral3'               : (205, 91, 69), 'coral4'               : (139, 62, 47),
    'cornflowerblue'       : (100,149,237), 'cornsilk'             : (255,248,220), 'cornsilk1'            : (255,248,220),
    'cornsilk2'            : (238,232,205), 'cornsilk3'            : (205,200,177), 'cornsilk4'            : (139,136,120),
    'cyan'                 : (  0,255,255), 'cyan1'                : (  0,255,255), 'cyan2'                : (  0,238,238),
    'cyan3'                : (  0,205,205), 'cyan4'                : (  0,139,139), 'darkblue'             : (  0,  0,139),
    'darkcyan'             : (  0,139,139), 'darkgoldenrod'        : (184,134, 11), 'darkgoldenrod1'       : (255,185, 15),
    'darkgoldenrod2'       : (238,173, 14), 'darkgoldenrod3'       : (205,149, 12), 'darkgoldenrod4'       : (139,101,  8),
    'darkgray'             : (169,169,169), 'darkgreen'            : (  0,100,  0), 'darkgrey'             : (169,169,169),
    'darkkhaki'            : (189,183,107), 'darkmagenta'          : (139,  0,139), 'darkolivegreen'       : ( 85,107, 47),
    'darkolivegreen1'      : (202,255,112), 'darkolivegreen2'      : (188,238,104), 'darkolivegreen3'      : (162,205, 90),
    'darkolivegreen4'      : (110,139, 61), 'darkorange'           : (255,140,  0), 'darkorange1'          : (255,127,  0),
    'darkorange2'          : (238,118,  0), 'darkorange3'          : (205,102,  0), 'darkorange4'          : (139, 69,  0),
    'darkorchid'           : (153, 50,204), 'darkorchid1'          : (191, 62,255), 'darkorchid2'          : (178, 58,238),
    'darkorchid3'          : (154, 50,205), 'darkorchid4'          : (104, 34,139), 'darkred'              : (139,  0,  0),
    'darksalmon'           : (233,150,122), 'darkseagreen'         : (143,188,143), 'darkseagreen1'        : (193,255,193),
    'darkseagreen2'        : (180,238,180), 'darkseagreen3'        : (155,205,155), 'darkseagreen4'        : (105,139,105),
    'darkslateblue'        : ( 72, 61,139), 'darkslategray'        : ( 47, 79, 79), 'darkslategray1'       : (151,255,255),
    'darkslategray2'       : (141,238,238), 'darkslategray3'       : (121,205,205), 'darkslategray4'       : ( 82,139,139),
    'darkslategrey'        : ( 47, 79, 79), 'darkturquoise'        : (  0,206,209), 'darkviolet'           : (148,  0,211),
    'deeppink'             : (255, 20,147), 'deeppink1'            : (255, 20,147), 'deeppink2'            : (238, 18,137),
    'deeppink3'            : (205, 16,118), 'deeppink4'            : (139, 10, 80), 'deepskyblue'          : (  0,191,255),
    'deepskyblue1'         : (  0,191,255), 'deepskyblue2'         : (  0,178,238), 'deepskyblue3'         : (  0,154,205),
    'deepskyblue4'         : (  0,104,139), 'dimgray'              : (105,105,105), 'dimgrey'              : (105,105,105),
    'dodgerblue'           : ( 30,144,255), 'dodgerblue1'          : ( 30,144,255), 'dodgerblue2'          : ( 28,134,238),
    'dodgerblue3'          : ( 24,116,205), 'dodgerblue4'          : ( 16, 78,139), 'firebrick'            : (178, 34, 34),
    'firebrick1'           : (255, 48, 48), 'firebrick2'           : (238, 44, 44), 'firebrick3'           : (205, 38, 38),
    'firebrick4'           : (139, 26, 26), 'floralwhite'          : (255,250,240), 'forestgreen'          : ( 34,139, 34),
    'gainsboro'            : (220,220,220), 'ghostwhite'           : (248,248,255), 'gold'                 : (255,215,  0),
    'gold1'                : (255,215,  0), 'gold2'                : (238,201,  0), 'gold3'                : (205,173,  0),
    'gold4'                : (139,117,  0), 'goldenrod'            : (218,165, 32), 'goldenrod1'           : (255,193, 37),
    'goldenrod2'           : (238,180, 34), 'goldenrod3'           : (205,155, 29), 'goldenrod4'           : (139,105, 20),
    'gray'                 : (190,190,190), 'gray0'                : (  0,  0,  0), 'gray1'                : (  3,  3,  3),
    'gray10'               : ( 26, 26, 26), 'gray100'              : (255,255,255), 'gray11'               : ( 28, 28, 28),
    'gray12'               : ( 31, 31, 31), 'gray13'               : ( 33, 33, 33), 'gray14'               : ( 36, 36, 36),
    'gray15'               : ( 38, 38, 38), 'gray16'               : ( 41, 41, 41), 'gray17'               : ( 43, 43, 43),
    'gray18'               : ( 46, 46, 46), 'gray19'               : ( 48, 48, 48), 'gray2'                : (  5,  5,  5),
    'gray20'               : ( 51, 51, 51), 'gray21'               : ( 54, 54, 54), 'gray22'               : ( 56, 56, 56),
    'gray23'               : ( 59, 59, 59), 'gray24'               : ( 61, 61, 61), 'gray25'               : ( 64, 64, 64),
    'gray26'               : ( 66, 66, 66), 'gray27'               : ( 69, 69, 69), 'gray28'               : ( 71, 71, 71),
    'gray29'               : ( 74, 74, 74), 'gray3'                : (  8,  8,  8), 'gray30'               : ( 77, 77, 77),
    'gray31'               : ( 79, 79, 79), 'gray32'               : ( 82, 82, 82), 'gray33'               : ( 84, 84, 84),
    'gray34'               : ( 87, 87, 87), 'gray35'               : ( 89, 89, 89), 'gray36'               : ( 92, 92, 92),
    'gray37'               : ( 94, 94, 94), 'gray38'               : ( 97, 97, 97), 'gray39'               : ( 99, 99, 99),
    'gray4'                : ( 10, 10, 10), 'gray40'               : (102,102,102), 'gray41'               : (105,105,105),
    'gray42'               : (107,107,107), 'gray43'               : (110,110,110), 'gray44'               : (112,112,112),
    'gray45'               : (115,115,115), 'gray46'               : (117,117,117), 'gray47'               : (120,120,120),
    'gray48'               : (122,122,122), 'gray49'               : (125,125,125), 'gray5'                : ( 13, 13, 13),
    'gray50'               : (127,127,127), 'gray51'               : (130,130,130), 'gray52'               : (133,133,133),
    'gray53'               : (135,135,135), 'gray54'               : (138,138,138), 'gray55'               : (140,140,140),
    'gray56'               : (143,143,143), 'gray57'               : (145,145,145), 'gray58'               : (148,148,148),
    'gray59'               : (150,150,150), 'gray6'                : ( 15, 15, 15), 'gray60'               : (153,153,153),
    'gray61'               : (156,156,156), 'gray62'               : (158,158,158), 'gray63'               : (161,161,161),
    'gray64'               : (163,163,163), 'gray65'               : (166,166,166), 'gray66'               : (168,168,168),
    'gray67'               : (171,171,171), 'gray68'               : (173,173,173), 'gray69'               : (176,176,176),
    'gray7'                : ( 18, 18, 18), 'gray70'               : (179,179,179), 'gray71'               : (181,181,181),
    'gray72'               : (184,184,184), 'gray73'               : (186,186,186), 'gray74'               : (189,189,189),
    'gray75'               : (191,191,191), 'gray76'               : (194,194,194), 'gray77'               : (196,196,196),
    'gray78'               : (199,199,199), 'gray79'               : (201,201,201), 'gray8'                : ( 20, 20, 20),
    'gray80'               : (204,204,204), 'gray81'               : (207,207,207), 'gray82'               : (209,209,209),
    'gray83'               : (212,212,212), 'gray84'               : (214,214,214), 'gray85'               : (217,217,217),
    'gray86'               : (219,219,219), 'gray87'               : (222,222,222), 'gray88'               : (224,224,224),
    'gray89'               : (227,227,227), 'gray9'                : ( 23, 23, 23), 'gray90'               : (229,229,229),
    'gray91'               : (232,232,232), 'gray92'               : (235,235,235), 'gray93'               : (237,237,237),
    'gray94'               : (240,240,240), 'gray95'               : (242,242,242), 'gray96'               : (245,245,245),
    'gray97'               : (247,247,247), 'gray98'               : (250,250,250), 'gray99'               : (252,252,252),
    'green'                : (  0,255,  0), 'green1'               : (  0,255,  0), 'green2'               : (  0,238,  0),
    'green3'               : (  0,205,  0), 'green4'               : (  0,139,  0), 'greenyellow'          : (173,255, 47),
    'grey'                 : (190,190,190), 'grey0'                : (  0,  0,  0), 'grey1'                : (  3,  3,  3),
    'grey10'               : ( 26, 26, 26), 'grey100'              : (255,255,255), 'grey11'               : ( 28, 28, 28),
    'grey12'               : ( 31, 31, 31), 'grey13'               : ( 33, 33, 33), 'grey14'               : ( 36, 36, 36),
    'grey15'               : ( 38, 38, 38), 'grey16'               : ( 41, 41, 41), 'grey17'               : ( 43, 43, 43),
    'grey18'               : ( 46, 46, 46), 'grey19'               : ( 48, 48, 48), 'grey2'                : (  5,  5,  5),
    'grey20'               : ( 51, 51, 51), 'grey21'               : ( 54, 54, 54), 'grey22'               : ( 56, 56, 56),
    'grey23'               : ( 59, 59, 59), 'grey24'               : ( 61, 61, 61), 'grey25'               : ( 64, 64, 64),
    'grey26'               : ( 66, 66, 66), 'grey27'               : ( 69, 69, 69), 'grey28'               : ( 71, 71, 71),
    'grey29'               : ( 74, 74, 74), 'grey3'                : (  8,  8,  8), 'grey30'               : ( 77, 77, 77),
    'grey31'               : ( 79, 79, 79), 'grey32'               : ( 82, 82, 82), 'grey33'               : ( 84, 84, 84),
    'grey34'               : ( 87, 87, 87), 'grey35'               : ( 89, 89, 89), 'grey36'               : ( 92, 92, 92),
    'grey37'               : ( 94, 94, 94), 'grey38'               : ( 97, 97, 97), 'grey39'               : ( 99, 99, 99),
    'grey4'                : ( 10, 10, 10), 'grey40'               : (102,102,102), 'grey41'               : (105,105,105),
    'grey42'               : (107,107,107), 'grey43'               : (110,110,110), 'grey44'               : (112,112,112),
    'grey45'               : (115,115,115), 'grey46'               : (117,117,117), 'grey47'               : (120,120,120),
    'grey48'               : (122,122,122), 'grey49'               : (125,125,125), 'grey5'                : ( 13, 13, 13),
    'grey50'               : (127,127,127), 'grey51'               : (130,130,130), 'grey52'               : (133,133,133),
    'grey53'               : (135,135,135), 'grey54'               : (138,138,138), 'grey55'               : (140,140,140),
    'grey56'               : (143,143,143), 'grey57'               : (145,145,145), 'grey58'               : (148,148,148),
    'grey59'               : (150,150,150), 'grey6'                : ( 15, 15, 15), 'grey60'               : (153,153,153),
    'grey61'               : (156,156,156), 'grey62'               : (158,158,158), 'grey63'               : (161,161,161),
    'grey64'               : (163,163,163), 'grey65'               : (166,166,166), 'grey66'               : (168,168,168),
    'grey67'               : (171,171,171), 'grey68'               : (173,173,173), 'grey69'               : (176,176,176),
    'grey7'                : ( 18, 18, 18), 'grey70'               : (179,179,179), 'grey71'               : (181,181,181),
    'grey72'               : (184,184,184), 'grey73'               : (186,186,186), 'grey74'               : (189,189,189),
    'grey75'               : (191,191,191), 'grey76'               : (194,194,194), 'grey77'               : (196,196,196),
    'grey78'               : (199,199,199), 'grey79'               : (201,201,201), 'grey8'                : ( 20, 20, 20),
    'grey80'               : (204,204,204), 'grey81'               : (207,207,207), 'grey82'               : (209,209,209),
    'grey83'               : (212,212,212), 'grey84'               : (214,214,214), 'grey85'               : (217,217,217),
    'grey86'               : (219,219,219), 'grey87'               : (222,222,222), 'grey88'               : (224,224,224),
    'grey89'               : (227,227,227), 'grey9'                : ( 23, 23, 23), 'grey90'               : (229,229,229),
    'grey91'               : (232,232,232), 'grey92'               : (235,235,235), 'grey93'               : (237,237,237),
    'grey94'               : (240,240,240), 'grey95'               : (242,242,242), 'grey96'               : (245,245,245),
    'grey97'               : (247,247,247), 'grey98'               : (250,250,250), 'grey99'               : (252,252,252),
    'honeydew'             : (240,255,240), 'honeydew1'            : (240,255,240), 'honeydew2'            : (224,238,224),
    'honeydew3'            : (193,205,193), 'honeydew4'            : (131,139,131), 'hotpink'              : (255,105,180),
    'hotpink1'             : (255,110,180), 'hotpink2'             : (238,106,167), 'hotpink3'             : (205, 96,144),
    'hotpink4'             : (139, 58, 98), 'indianred'            : (205, 92, 92), 'indianred1'           : (255,106,106),
    'indianred2'           : (238, 99, 99), 'indianred3'           : (205, 85, 85), 'indianred4'           : (139, 58, 58),
    'ivory'                : (255,255,240), 'ivory1'               : (255,255,240), 'ivory2'               : (238,238,224),
    'ivory3'               : (205,205,193), 'ivory4'               : (139,139,131), 'khaki'                : (240,230,140),
    'khaki1'               : (255,246,143), 'khaki2'               : (238,230,133), 'khaki3'               : (205,198,115),
    'khaki4'               : (139,134, 78), 'lavender'             : (230,230,250), 'lavenderblush'        : (255,240,245),
    'lavenderblush1'       : (255,240,245), 'lavenderblush2'       : (238,224,229), 'lavenderblush3'       : (205,193,197),
    'lavenderblush4'       : (139,131,134), 'lawngreen'            : (124,252,  0), 'lemonchiffon'         : (255,250,205),
    'lemonchiffon1'        : (255,250,205), 'lemonchiffon2'        : (238,233,191), 'lemonchiffon3'        : (205,201,165),
    'lemonchiffon4'        : (139,137,112), 'lightblue'            : (173,216,230), 'lightblue1'           : (191,239,255),
    'lightblue2'           : (178,223,238), 'lightblue3'           : (154,192,205), 'lightblue4'           : (104,131,139),
    'lightcoral'           : (240,128,128), 'lightcyan'            : (224,255,255), 'lightcyan1'           : (224,255,255),
    'lightcyan2'           : (209,238,238), 'lightcyan3'           : (180,205,205), 'lightcyan4'           : (122,139,139),
    'lightgoldenrod'       : (238,221,130), 'lightgoldenrod1'      : (255,236,139), 'lightgoldenrod2'      : (238,220,130),
    'lightgoldenrod3'      : (205,190,112), 'lightgoldenrod4'      : (139,129, 76), 'lightgoldenrodyellow' : (250,250,210),
    'lightgray'            : (211,211,211), 'lightgreen'           : (144,238,144), 'lightgrey'            : (211,211,211),
    'lightpink'            : (255,182,193), 'lightpink1'           : (255,174,185), 'lightpink2'           : (238,162,173),
    'lightpink3'           : (205,140,149), 'lightpink4'           : (139, 95,101), 'lightsalmon'          : (255,160,122),
    'lightsalmon1'         : (255,160,122), 'lightsalmon2'         : (238,149,114), 'lightsalmon3'         : (205,129, 98),
    'lightsalmon4'         : (139, 87, 66), 'lightseagreen'        : ( 32,178,170), 'lightskyblue'         : (135,206,250),
    'lightskyblue1'        : (176,226,255), 'lightskyblue2'        : (164,211,238), 'lightskyblue3'        : (141,182,205),
    'lightskyblue4'        : ( 96,123,139), 'lightslateblue'       : (132,112,255), 'lightslategray'       : (119,136,153),
    'lightslategrey'       : (119,136,153), 'lightsteelblue'       : (176,196,222), 'lightsteelblue1'      : (202,225,255),
    'lightsteelblue2'      : (188,210,238), 'lightsteelblue3'      : (162,181,205), 'lightsteelblue4'      : (110,123,139),
    'lightyellow'          : (255,255,224), 'lightyellow1'         : (255,255,224), 'lightyellow2'         : (238,238,209),
    'lightyellow3'         : (205,205,180), 'lightyellow4'         : (139,139,122), 'limegreen'            : ( 50,205, 50),
    'linen'                : (250,240,230), 'magenta'              : (255,  0,255), 'magenta1'             : (255,  0,255),
    'magenta2'             : (238,  0,238), 'magenta3'             : (205,  0,205), 'magenta4'             : (139,  0,139),
    'maroon'               : (176, 48, 96), 'maroon1'              : (255, 52,179), 'maroon2'              : (238, 48,167),
    'maroon3'              : (205, 41,144), 'maroon4'              : (139, 28, 98), 'mediumaquamarine'     : (102,205,170),
    'mediumblue'           : (  0,  0,205), 'mediumorchid'         : (186, 85,211), 'mediumorchid1'        : (224,102,255),
    'mediumorchid2'        : (209, 95,238), 'mediumorchid3'        : (180, 82,205), 'mediumorchid4'        : (122, 55,139),
    'mediumpurple'         : (147,112,219), 'mediumpurple1'        : (171,130,255), 'mediumpurple2'        : (159,121,238),
    'mediumpurple3'        : (137,104,205), 'mediumpurple4'        : ( 93, 71,139), 'mediumseagreen'       : ( 60,179,113),
    'mediumslateblue'      : (123,104,238), 'mediumspringgreen'    : (  0,250,154), 'mediumturquoise'      : ( 72,209,204),
    'mediumvioletred'      : (199, 21,133), 'midnightblue'         : ( 25, 25,112), 'mintcream'            : (245,255,250),
    'mistyrose'            : (255,228,225), 'mistyrose1'           : (255,228,225), 'mistyrose2'           : (238,213,210),
    'mistyrose3'           : (205,183,181), 'mistyrose4'           : (139,125,123), 'moccasin'             : (255,228,181),
    'navajowhite'          : (255,222,173), 'navajowhite1'         : (255,222,173), 'navajowhite2'         : (238,207,161),
    'navajowhite3'         : (205,179,139), 'navajowhite4'         : (139,121, 94), 'navy'                 : (  0,  0,128),
    'navyblue'             : (  0,  0,128), 'oldlace'              : (253,245,230), 'olivedrab'            : (107,142, 35),
    'olivedrab1'           : (192,255, 62), 'olivedrab2'           : (179,238, 58), 'olivedrab3'           : (154,205, 50),
    'olivedrab4'           : (105,139, 34), 'orange'               : (255,165,  0), 'orange1'              : (255,165,  0),
    'orange2'              : (238,154,  0), 'orange3'              : (205,133,  0), 'orange4'              : (139, 90,  0),
    'orangered'            : (255, 69,  0), 'orangered1'           : (255, 69,  0), 'orangered2'           : (238, 64,  0),
    'orangered3'           : (205, 55,  0), 'orangered4'           : (139, 37,  0), 'orchid'               : (218,112,214),
    'orchid1'              : (255,131,250), 'orchid2'              : (238,122,233), 'orchid3'              : (205,105,201),
    'orchid4'              : (139, 71,137), 'palegoldenrod'        : (238,232,170), 'palegreen'            : (152,251,152),
    'palegreen1'           : (154,255,154), 'palegreen2'           : (144,238,144), 'palegreen3'           : (124,205,124),
    'palegreen4'           : ( 84,139, 84), 'paleturquoise'        : (175,238,238), 'paleturquoise1'       : (187,255,255),
    'paleturquoise2'       : (174,238,238), 'paleturquoise3'       : (150,205,205), 'paleturquoise4'       : (102,139,139),
    'palevioletred'        : (219,112,147), 'palevioletred1'       : (255,130,171), 'palevioletred2'       : (238,121,159),
    'palevioletred3'       : (205,104,137), 'palevioletred4'       : (139, 71, 93), 'papayawhip'           : (255,239,213),
    'peachpuff'            : (255,218,185), 'peachpuff1'           : (255,218,185), 'peachpuff2'           : (238,203,173),
    'peachpuff3'           : (205,175,149), 'peachpuff4'           : (139,119,101), 'peru'                 : (205,133, 63),
    'pink'                 : (255,192,203), 'pink1'                : (255,181,197), 'pink2'                : (238,169,184),
    'pink3'                : (205,145,158), 'pink4'                : (139, 99,108), 'plum'                 : (221,160,221),
    'plum1'                : (255,187,255), 'plum2'                : (238,174,238), 'plum3'                : (205,150,205),
    'plum4'                : (139,102,139), 'powderblue'           : (176,224,230), 'purple'               : (160, 32,240),
    'purple1'              : (155, 48,255), 'purple2'              : (145, 44,238), 'purple3'              : (125, 38,205),
    'purple4'              : ( 85, 26,139), 'red'                  : (255,  0,  0), 'red1'                 : (255,  0,  0),
    'red2'                 : (238,  0,  0), 'red3'                 : (205,  0,  0), 'red4'                 : (139,  0,  0),
    'rosybrown'            : (188,143,143), 'rosybrown1'           : (255,193,193), 'rosybrown2'           : (238,180,180),
    'rosybrown3'           : (205,155,155), 'rosybrown4'           : (139,105,105), 'royalblue'            : ( 65,105,225),
    'royalblue1'           : ( 72,118,255), 'royalblue2'           : ( 67,110,238), 'royalblue3'           : ( 58, 95,205),
    'royalblue4'           : ( 39, 64,139), 'saddlebrown'          : (139, 69, 19), 'salmon'               : (250,128,114),
    'salmon1'              : (255,140,105), 'salmon2'              : (238,130, 98), 'salmon3'              : (205,112, 84),
    'salmon4'              : (139, 76, 57), 'sandybrown'           : (244,164, 96), 'seagreen'             : ( 46,139, 87),
    'seagreen1'            : ( 84,255,159), 'seagreen2'            : ( 78,238,148), 'seagreen3'            : ( 67,205,128),
    'seagreen4'            : ( 46,139, 87), 'seashell'             : (255,245,238), 'seashell1'            : (255,245,238),
    'seashell2'            : (238,229,222), 'seashell3'            : (205,197,191), 'seashell4'            : (139,134,130),
    'sienna'               : (160, 82, 45), 'sienna1'              : (255,130, 71), 'sienna2'              : (238,121, 66),
    'sienna3'              : (205,104, 57), 'sienna4'              : (139, 71, 38), 'skyblue'              : (135,206,235),
    'skyblue1'             : (135,206,255), 'skyblue2'             : (126,192,238), 'skyblue3'             : (108,166,205),
    'skyblue4'             : ( 74,112,139), 'slateblue'            : (106, 90,205), 'slateblue1'           : (131,111,255),
    'slateblue2'           : (122,103,238), 'slateblue3'           : (105, 89,205), 'slateblue4'           : ( 71, 60,139),
    'slategray'            : (112,128,144), 'slategray1'           : (198,226,255), 'slategray2'           : (185,211,238),
    'slategray3'           : (159,182,205), 'slategray4'           : (108,123,139), 'slategrey'            : (112,128,144),
    'snow'                 : (255,250,250), 'snow1'                : (255,250,250), 'snow2'                : (238,233,233),
    'snow3'                : (205,201,201), 'snow4'                : (139,137,137), 'springgreen'          : (  0,255,127),
    'springgreen1'         : (  0,255,127), 'springgreen2'         : (  0,238,118), 'springgreen3'         : (  0,205,102),
    'springgreen4'         : (  0,139, 69), 'steelblue'            : ( 70,130,180), 'steelblue1'           : ( 99,184,255),
    'steelblue2'           : ( 92,172,238), 'steelblue3'           : ( 79,148,205), 'steelblue4'           : ( 54,100,139),
    'tan'                  : (210,180,140), 'tan1'                 : (255,165, 79), 'tan2'                 : (238,154, 73),
    'tan3'                 : (205,133, 63), 'tan4'                 : (139, 90, 43), 'thistle'              : (216,191,216),
    'thistle1'             : (255,225,255), 'thistle2'             : (238,210,238), 'thistle3'             : (205,181,205),
    'thistle4'             : (139,123,139), 'tomato'               : (255, 99, 71), 'tomato1'              : (255, 99, 71),
    'tomato2'              : (238, 92, 66), 'tomato3'              : (205, 79, 57), 'tomato4'              : (139, 54, 38),
    'turquoise'            : ( 64,224,208), 'turquoise1'           : (  0,245,255), 'turquoise2'           : (  0,229,238),
    'turquoise3'           : (  0,197,205), 'turquoise4'           : (  0,134,139), 'violet'               : (238,130,238),
    'violetred'            : (208, 32,144), 'violetred1'           : (255, 62,150), 'violetred2'           : (238, 58,140),
    'violetred3'           : (205, 50,120), 'violetred4'           : (139, 34, 82), 'wheat'                : (245,222,179),
    'wheat1'               : (255,231,186), 'wheat2'               : (238,216,174), 'wheat3'               : (205,186,150),
    'wheat4'               : (139,126,102), 'white'                : (255,255,255), 'whitesmoke'           : (245,245,245),
    'yellow'               : (255,255,  0), 'yellow1'              : (255,255,  0), 'yellow2'              : (238,238,  0),
    'yellow3'              : (205,205,  0), 'yellow4'              : (139,139,  0), 'yellowgreen'          : (154,205, 50),
  }

  def __init__(self, colorChoice='White'):
    """
    Create a new instance of Color.

    The parameter can be either:
       - a string with the name of the color
       - an (r,g,b) tuple
       - an existing Color instance (which will be cloned)

    It defaults to 'White'
    """
    # we intentionally have Drawable objects using a color
    # register with the color instance, so that when the color is
    # muated, the object can be informed that it has changed
    self._drawables = []
    
    if isinstance(colorChoice,str):
      try:
        self.setByName(colorChoice)
      except ValueError, ve:
        raise ValueError, str(ve)
    elif isinstance(colorChoice,tuple):
      try:
        self.setByValue(colorChoice)
      except ValueError, ve:
        raise ValueError, str(ve)
    elif isinstance(colorChoice,Color):
      self._colorName = colorChoice._colorName
      self._transparent = colorChoice._transparent
      self._colorValue = colorChoice._colorValue
    else:
      raise TypeError, 'Invalid color specification'

  def randomColor():
    return Color((_ourRandom.randrange(0,256),_ourRandom.randrange(0,256),_ourRandom.randrange(0,256)))
  randomColor = staticmethod(randomColor)

  def setByName(self, colorName):
    """
    Set the color to colorName.

    colorName   a string representing a valid name
    
    It colorName is 'Transparent' the resulting color will not
    show up on a canvas.
    """
    if not isinstance(colorName,str):
      raise TypeError, 'string expected as color name'

    self._colorName = colorName.lower().replace(' ','')
    if self._colorName == 'transparent':
      self._transparent = True
      self._colorValue = (0,0,0)
    else:
      try:
        self._transparent = False
        self._colorValue = Color._colorValues[self._colorName.lower()]
      except KeyError:
        raise ValueError, '%s is not a valid color name' % colorName
    self._informDrawables()

  def getColorName(self):
    """
    Returns the name of the color.

    If the color was set by RGB value, it returns 'Custom'.
    """
    return self._colorName

  def setByValue(self, rgbTuple):
    """
    Sets the color to the given tuple of (red, green, blue) values.
    """
    if not isinstance(rgbTuple,tuple):
      raise TypeError, '(r,g,b) tuple expected'
    if len(rgbTuple)!=3:
      raise ValueError, '(r,g,b) tuple must have three components'
    self._transparent = False
    self._colorName = 'Custom'
    self._colorValue = rgbTuple
    self._informDrawables()

  def getColorValue(self):
    """
    Returns a tuple of the (red, green, blue) color components.
    """
    return (self._colorValue[0], self._colorValue[1], self._colorValue[2])

  def isTransparent(self):
    """
    Returns a boolean variable indicating if the current color is transparent.

    A return value of True indicates the color is not visibile.
    """
    return self._transparent

  def __repr__(self):
    """
    Returns the name of the color, if named.  Otherwise returns the (r,g,b) value.
    """
    if self._colorName == 'Custom':
      return self._colorValue.__repr__()
    else:
      return self._colorName

  def _register(self, drawable):
    """
    Called to register a drawable with this color instance
    """
    if drawable not in self._drawables:
      self._drawables.append(drawable)
  
  def _unregister(self, drawable):
    """
    Called to unregister a drawable with this color instance
    """
    if drawable in self._drawables:
      self._drawables.remove(drawable)
  
  def _informDrawables(self):
    """
    When the color instance has been mutated, we must inform those registered drawables.
    """
    for drawable in self._drawables:
      drawable._objectChanged()

class _SortedSet(list):
  def __init__(self, initial=None):
    list.__init__(self)  # calls the parent class constructor
    if initial:
      self.extend(initial)

  def indexAfter(self, value):
    index = 0
    while index < len(self) and value >= self[index]:
      index += 1
    return index

  def insert(self, value):
    if value not in self:
      index = self.indexAfter(value)
      list.insert(self, index, value)   # the parent's method
      
  def append(self, object):
    self.insert(object)

  def extend(self, other):
    for element in other:
      self.insert(element)
    
  def __add__(self, other):
    result = _SortedSet(self)  # creates new copy of self
    result.extend(other)
    return result

  def sort(self):
    pass
  
class _Container(object):
  def __init__(self):
    self._contents = []

  def __contains__(self, obj):
    return obj in self._contents

  def add(self, drawable):
    """
    Add the drawable object to the container.
    """
    # not doing error checking here, as we want tailored messages for Canvas and Layer
    self._contents.append(drawable)

  def remove(self, drawable):
    """
    Removes the drawable object from the container.
    """
    # not doing error checking here, as we want tailored messages for Canvas and Layer
    self._contents.remove(drawable)

  def clear(self):
    """
    Removes all objects from the container.
    """
    contents = list(self._contents)  # intentional clone
    for drawable in contents:
      self.remove(drawable)

  def getContents(self):
    """
    Returns the contents of the container sorted by depth.
    """
    contentsPair = list()
    for drawable in self._contents:
      contentsPair.append( (drawable._depth, drawable) )
    contentsPair.sort()
    contentsPair.reverse()

    if _debug >= 3:
      print "Contents of container (depth, item):", contentsPair

    contents = list()
    for pair in contentsPair:
      contents.append(pair[1])

    return contents

class Event(object):
  def __init__(self):
    self._eventType = ""
    self._x, self._y = 0, 0
    self._prevx, self._prevy = 0,0
    self._key = ""
    
  def getType(self):
    return self._eventType
    
  def getMouseLocation(self):
    return Point(self._x, self._y)
  
  def getPrevMouseLocation(self):
    return Point(self._prevx, self._prevy)

class EventHandler(object):
  def __init__(self):
    pass

  def handle(self, event):
    pass

class ReleaseHandler(EventHandler):
  def __init__(self, lock):
    self._lock = lock
    self._event = None
    self._lock.acquire()

  def handle(self, event):
    self._event = event
    print "Releasing"
    self._lock.release()

class EventTrigger(object):

  def __init__(self):
    pass

  def wait(self):
    """
    Wait for an event to occur.

    When an event occurs and Event instance is returned
    with information about what has happened.
    """
    lock = _threading.Lock()
    rh = ReleaseHandler(lock)
    self.addHandler(rh)
    lock.acquire()
    self.removeHandler(rh)
    return rh._event

  def addHandler(self, handler):
    _graphicsManager.addHandler(self, handler)

  def removeHandler(self, handler):
    _graphicsManager.removeHandler(self, handler)

class Canvas(_Container, EventTrigger):
  """
  Represents a window which can be drawn upon.
  """

  def __init__(self, w=200, h=200, background=None, title="Graphics canvas", autoRefresh=True):
    """
    Create a new drawing canvas.

    A new canvas will be created.
      w         width of drawing area (defaults to 200)
      h         height of drawing area (defaults to 200)
      background    color of the background (defaults to White)
      title       window title (defaults to "Graphics Canvas")
      autoRefresh   whether auto-refresh mode is used (default to True)
    """
    global _graphicsManager
    _Container.__init__(self)
    EventTrigger.__init__(self)

    # Create the underlying graphics manager if necessary
    if _graphicsManager == None:
      _graphicsManager = _UnderlyingManager()
      _graphicsManager.start()
    elif _graphicsManager._referenceCount == 0:
      _graphicsManager.start()
    else:
      _graphicsManager._referenceCount += 1
    
    if not background:
      background = 'white'

    if not isinstance(w, (int,float)):
      raise TypeError, 'numeric value expected for width'
    if not isinstance(h, (int,float)):
      raise TypeError, 'numeric value expected for height'
    if not isinstance(title,str):
      raise TypeError, 'string expected as title'
    if not isinstance(autoRefresh,bool):
      raise TypeError, 'autoRefresh flag should be a bool'
    
    if isinstance(background,Color):
      self._backgroundColor = color
    else:
      try:
        self._backgroundColor = Color(background)
      except TypeError,te:
        raise TypeError,str(te)
      except ValueError,ve:
        raise ValueError,str(ve)

    self._width = w
    self._height = h
    self._title = title
    self._autoRefresh = autoRefresh
    
    _graphicsManager.addCommandToQueue(('create canvas', self, w, h, self._backgroundColor, title, autoRefresh), True)
      
  def setBackgroundColor(self, backgroundColor):
    """
    Set the background color.

    The parameter can be either:
       - a string with the name of the color
       - an (r,g,b) tuple
       - an existing Color instance
    """
    if isinstance(backgroundColor,Color):
      self._backgroundColor = backgroundColor
    else:
      try:
        self._backgroundColor = Color(backgroundColor)
      except TypeError,te:
        raise TypeError,str(te)
      except ValueError,ve:
        raise ValueError,str(ve)
    if self._autoRefresh:
      self.refresh()

  def getBackgroundColor(self):
    """
    Returns the background color as an instance of Color.
    """
    return self._backgroundColor
    
  def setWidth(self, w):
    """
    Resets the canvas width to w.
    """
    if not isinstance(w, (int,float)):
      raise TypeError, 'numeric value expected for width'
    if w<=0:
      raise ValueError, 'width must be positive'
    self._width = w
    if self._autoRefresh:
      self.refresh()

  def getWidth(self):
    """
    Get the width of the canvas.
    """
    return self._width

  def setHeight(self, h):
    """
    Resets the canvas height to h.
    """
    if not isinstance(h, (int,float)):
      raise TypeError, 'numeric value expected for height'
    if h<=0:
      raise ValueError, 'height must be positive'
    self._height = h
    if self._autoRefresh:
      self.refresh()

  def getHeight(self):
    """
    Get the height of the canvas.
    """
    return self._height

  def setTitle(self, title):
    """
    Set the title for the canvas window.
    """
    if not isinstance(title,str):
      raise TypeError, 'string expected as title'
    self._title = title
    if self._autoRefresh:
      self.refresh()

  def getTitle(self):
    """
    Get the title of the window.
    """
    return self._title

  def close(self):
    """
    Close the canvas window (if not already closed).
    """
    global _graphicsManager
    self._canvas.close()
    _graphicsManager._referenceCount -= 1
    if _graphicsManager._referenceCount == 0:
      _graphicsManager.stop()
      _graphicsManager = None
      
  def open(self):
    """
    Opens a graphic window (if not already open).
    """
    self._canvas.open()

  def add(self, drawable):
    """
    Add the drawable object to the canvas.
    """
    if not isinstance(drawable,Drawable):
      raise TypeError, 'can only add Drawable objects to a Canvas'
    if drawable in self._contents:
      raise ValueError, 'object already on the Canvas'
    _Container.add(self, drawable)
    
    if self._autoRefresh:
      self.refresh()

  def remove(self, drawable):
    """
    Removes the drawable object from the canvas.
    """
    if drawable not in self._contents:
      raise ValueError, 'object not currently on the Canvas'
    _Container.remove(self, drawable)
    _graphicsManager.objectChanged(drawable)

  def setAutoRefresh(self, autoRefresh=True):
    """
    Change the auto-refresh mode to either True or False.

    When True (the default), every change to the canvas or to an
       object drawn upon the canvas will be immediately rendered to
       the screen.

    When False, all changes are recorded internally, yet not shown
    on the screen until the next subsequent call to the refresh()
    method of this canvas.  This allows multiple changes to be
    buffered and rendered all at once.
    """
    if not isinstance(autoRefresh,bool):
      raise TypeError, 'autoRefresh flag should be a bool'
    if autoRefresh and not self._autoRefresh:
      self.refresh()  # flush the current queue
    self._autoRefresh = autoRefresh

  def refresh(self, force=False):
    """
    Forces all internal changes to be rendered to the screen.

    This method is only necessary when the auto-refresh property
    of the canvas has previously been turned off.  If force is
    True then the entire window is redraw regardless of need.
    """
    _graphicsManager.addCommandToQueue(("begin refresh", self, force))
    _graphicsManager.addCommandToQueue(("update canvas", self, self._height, self._width, self._backgroundColor, self._title), True)
    for drawable in self.getContents():
      drawable._draw()
    _graphicsManager.addCommandToQueue(("complete refresh", self), True)

  def saveToFile(self, filename):
    """
    Saves a picture of the current canvas to a file.
    """
    self._canvas.saveToFile(filename)
    
class Drawable(EventTrigger):
  """
  An object that can be drawn to a graphics canvas.
  """
  
  def __init__(self, reference=None):
    """
    Creates an instance of Drawable.

    referencePoint  local reference point for scaling and rotating
            (Defaults to Point(0,0) if None specified)
    """
    EventTrigger.__init__(self)

    if reference:
      if not isinstance(reference,Point):
        raise TypeError, 'reference point must be a Point instance'
      self._reference = reference
    else:
      self._reference = Point()
    self._transform = Transformation()
    self._depth = [50, _ourRandom.random()]

  def move(self, dx, dy):
    """
    Move the object dx units to the right and dy units down.

    Negative values move the object left or up.
    """
    if not isinstance(dx, (int,float)):
      raise TypeError, 'dx must be numeric'
    if not isinstance(dy, (int,float)):
      raise TypeError, 'dy must be numeric'
    self._transform = Transformation( (1.,0.,0.,1.,dx,dy)) * self._transform
    self._objectChanged()

  def moveTo(self, x, y):
    """
    Move the object to align its reference point with (x,y)
    """
    if not isinstance(x, (int,float)):
      raise TypeError, 'x must be numeric'
    if not isinstance(y, (int,float)):
      raise TypeError, 'y must be numeric'
    curRef = self.getReferencePoint()
    self.move(x-curRef.getX(), y-curRef.getY())
    self._objectChanged()

  def rotate(self, angle):
    """
    Rotates the object around its current reference point.

    angle  number of degrees of rotation (clockwise)
    """
    if not isinstance(angle, (int,float)):
      raise TypeError, 'angle must be specified numerically'
    angle = -_math.pi*angle/180.
    p = self._localToGlobal(self._reference)
    trans = Transformation((1.,0.,0.,1.)+p.get())
    rot = Transformation((_math.cos(angle),_math.sin(angle),
                -_math.sin(angle),_math.cos(angle),0.,0.))
    
    self._transform = trans*(rot*(trans.inv()*self._transform))
    self._objectChanged()

  def scale(self, factor):
    """
    Scales the object relative to its current reference point.

    factor  scale is multiplied by this number (must be positive)
    """
    if not isinstance(factor, (int,float)):
      raise TypeError, 'scaling factor must be a positive number'
    if factor<=0:
      raise ValueError, 'scaling factor must be a positive number'
    p = self._localToGlobal(self._reference)
    trans = Transformation((1.,0.,0.,1.)+p.get())
    sca = Transformation((factor,0.,0.,factor,0.,0.))

    self._transform = trans*(sca*(trans.inv()*self._transform))
    self._objectChanged()
    
  def flip(self, angle):
    
    if not isinstance(angle, (int,float)):
      raise TypeError, 'scaling factor must be a positive number'
    
    angle = -_math.pi*angle/180.
    p = self._localToGlobal(self._reference)
    trans = Transformation((1.,0.,0.,1.)+p.get())
    rot = Transformation((_math.cos(angle),_math.sin(angle),
                -_math.sin(angle),_math.cos(angle),0.,0.))
    rotinv = rot.inv()
    invert = Transformation((-1.,0.,0.,1.,0.,0.))
    
    self._transform = trans*(rotinv*(invert*(rot*(trans.inv()*self._transform))))
    self._objectChanged()

  def getReferencePoint(self):
    """
    Return a copy of the current reference point placement.

    Note that mutating that copy has no effect on the drawable object.
    """
    return self._localToGlobal(self._reference)

  def adjustReference(self, dx, dy):
    """
    Move the local reference point relative to its current position.

    Note that the object is not moved at all.
    """
    if not isinstance(dx, (int,float)):
      raise TypeError, 'dx must be numeric'
    if not isinstance(dy, (int,float)):
      raise TypeError, 'dy must be numeric'
    p = self._localToGlobal(self._reference)
    p = Point(p.getX()+dx, p.getY()+dy)
    self._reference = self._globalToLocal(p)
    self._objectChanged()

  def setDepth(self, depth):
    """
    Sets the depth of the object.

    Objects with a higher depth will be rendered behind those with lower depths.
    """
    if not isinstance(depth, (int,float)):
      raise TypeError, 'depth must be numeric'
    self._depth[-2] = depth
    self._objectChanged()

  def getDepth(self):
    """
    Returns the depth of the object.
    """
    return self._depth[-2]

  def clone(self):
    """
    Return an exact duplicate of the drawable object.
    """
    return _copy.deepcopy(self)

  def _localToGlobal(self, point):
    if not isinstance(point,Point):
      raise TypeError, 'parameter must be a Point instance'
    return self._transform.image(point)

  def _globalToLocal(self, point):
    if not isinstance(point,Point):
      raise TypeError, 'parameter must be a Point instance'
    return self._transform.inv().image(point)

  def _beginDraw(self):
    _graphicsManager.addCommandToQueue(("begin draw", self))

  def _completeDraw(self):
    _graphicsManager.addCommandToQueue(("complete draw", self))

  def _draw(self):
    """
    Causes the object to be drawn (typically, the method is not called directly).
    """
    if _debug>=2:
      print "within Drawable._draw for self=",self

  def _objectChanged(self):
    """
    Some trait of this object has been mutated and so all of its
    rendered images may need to be updated.
    """
    if _graphicsManager:
      _graphicsManager.objectChanged(self)

class Layer(Drawable, _Container):
  """
  Stores a group of shapes that act as one drawable object.

  Objects are placed onto the layer relative to the coordinate
  system of the layer itself.  The layer can then be placed onto a
  canvas (or even onto another layer).
  """
  def __init__(self):
    """
    Construct a new instance of Layer.

    The layer is initially empty.
    
    The reference point of that layer is initially the origin in
    its own coordinate system, (0,0).
    """
    Drawable.__init__(self)
    _Container.__init__(self)
      

  def add(self, drawable):
    """
    Add the drawable object to the layer.
    """
    if _debug>=2: print 'Call to Layer.add with self=',self,' drawable=',drawable
    if not isinstance(drawable,Drawable):
      raise TypeError, 'can only add Drawable objects to a Layer'
    if drawable in self._contents:
      raise ValueError, 'object already on the Layer'
    
    _Container.add(self, drawable)
    self._objectChanged()
    
  def remove(self, drawable):
    """
    Removes the drawable object from the layer.
    """
    if drawable not in self._contents:
      raise ValueError, 'object not currently on the Layer'
    
    _Container.remove(self,drawable)
    self._objectChanged()

  def _draw(self):
    self._beginDraw()

    for shape in self.getContents():
      shape._draw()

    self._completeDraw()
          

class Shape(Drawable):
  """
  Represents objects that are drawable and have a border.
  """
  
  def __init__(self, reference=None):
    """
    Construct an instance of Shape.

    reference  the initial placement of the shape's reference point.
           (Defaults to Point(0,0) if None specified)
    """
    if reference and not isinstance(reference,Point):
      raise TypeError, 'reference point must be a Point instance'
    Drawable.__init__(self, reference)
    self._borderColor = Color("Black")
    self._borderWidth = 1

  def setBorderColor(self, borderColor):
    """
    Set the border color to a copy of borderColor.

    The parameter can be either:
       - a string with the name of the color
       - an (r,g,b) tuple
       - an existing Color instance
    """
    old = self._borderColor
    if isinstance(borderColor,Color):
      self._borderColor = borderColor
    else:
      try:
        self._borderColor = Color(borderColor)
      except TypeError,te:
        raise TypeError,str(te)
      except ValueError,ve:
        raise ValueError,str(ve)
    self._objectChanged()

    if self._borderColor is not old:
      self._borderColor._register(self)
      if not isinstance(self,FillableShape) or old is not self._fillColor:
        # this shape no longer using the old color
        old._unregister(self)

  def getBorderColor(self):
    """
    Return the color of the object's border.
    """
    return self._borderColor

  def setBorderWidth(self, borderWidth):
    """
    Set the width of the border to borderWidth.
    """
    if not isinstance(borderWidth, (int,float)):
      raise TypeError, 'Border width must be non-negative number'
    if borderWidth < 0:
      raise ValueError, "A shape's border width cannot be negative."
    self._borderWidth = borderWidth
    self._objectChanged()

  def getBorderWidth(self):
    """
    Returns the width of the border.
    """
    return self._borderWidth

  def draw(self):
    pass

    
class FillableShape(Shape):
  """
  A shape that can be filled in.
  """
  def __init__(self, reference=None):
    """
    Construct a new instance of Shape.

    The interior color defaults to 'transparent'.

    reference  the initial placement of the shape's reference point.
           (Defaults to Point(0,0) if None specified)
    """
    if reference and not isinstance(reference,Point):
      raise TypeError, 'reference point must be a Point instance'
    Shape.__init__(self, reference)
    self._fillColor = Color("Transparent")

  def setFillColor(self, color):
    """
    Set the interior color of the shape to the color.

    The parameter can be either:
       - a string with the name of the color
       - an (r,g,b) tuple
       - an existing Color instance
    """
    old = self._fillColor
    if isinstance(color,Color):
      self._fillColor = color
    else:
      try:
        self._fillColor = Color(color)
      except TypeError,te:
        raise TypeError,str(te)
      except ValueError,ve:
        raise ValueError,str(ve)
    self._objectChanged()

    if self._fillColor is not old:
      self._fillColor._register(self)
      if self._borderColor is not old:
        # no longer using the old color
        old._unregister(self)


  def getFillColor(self):
    """
    Return the color of the shape's interior.
    """
    return self._fillColor
  
  def draw(self):
    pass

class Circle(FillableShape):
  """
  A circle that can be drawn to a canvas.
  """
  def __init__(self, radius=10, center=None):
    """
    Construct a new instance of Circle.

    radius  the circle's radius.  (Defaults to 10)
    center  a Point representing the placement of the circle's center
        (Defaults to Point(0,0) )

    The reference point for a circle is originally its center.
    """
    if not isinstance(radius, (int,float)):
      raise TypeError, 'Radius must be a number'
    if radius <= 0:
      raise ValueError, "The circle's radius must be positive."
    if center and not isinstance(center,Point):
      raise TypeError, 'center must be specified as a Point'

    FillableShape.__init__(self) # intentionally not sending center
    if not center:
      center = Point()
    self._transform = Transformation( (radius,0.,0.,radius,center.getX(),center.getY()) )

  def setRadius(self, radius):
    """
    Set the radius of the circle to radius.
    """
    if not isinstance(radius, (int,float)):
      raise TypeError, 'Radius must be a number'
    if radius <= 0:
      raise ValueError, "The circle's radius must be positive."

    factor = float(radius)/self.getRadius()
    self._transform = self._transform * Transformation((factor,0.,0.,factor,0.,0.))
    
    self._objectChanged()
    
  def getRadius(self):
    """
    Returns the radius of the circle.
    """
    return _math.sqrt(self._transform._matrix[0]**2 + self._transform._matrix[1]**2)

  def _draw(self):
    self._beginDraw()

    _graphicsManager.addCommandToQueue(('draw circle', self))
    FillableShape._draw(self)
      
    self._completeDraw()
     
class Rectangle(FillableShape):
  """
  A rectangle that can be drawn to the canvas.
  """
  def __init__(self, width=20, height=10, center=None):
    """
    Construct a new instance of a Rectangle.

    The reference point for a rectangle is its center.

    width     the width of the rectangle.  (Defaults to 20)
    height    the height of the rectangle.  (Defaults to 10)
    center    a Point representing the placement of the rectangle's center
          (Defaults to Point(0,0) )
    """
    if not isinstance(width, (int,float)):
      raise TypeError, 'Width must be a number'
    if width <= 0:
      raise ValueError, "The width must be positive."
    if not isinstance(height, (int,float)):
      raise TypeError, 'Height must be a number'
    if height <= 0:
      raise ValueError, "The height must be positive."
    if center and not isinstance(center,Point):
      raise TypeError, 'center must be specified as a Point'

    FillableShape.__init__(self)  # intentionally not sending center point

    if not center:
      center = Point(0,0)

    self._transform = Transformation( (width, 0., 0., height, center.getX(), center.getY()) )

  def getWidth(self):
    """
    Returns the width of the rectangle.
    """
    return _math.sqrt(self._transform._matrix[0]**2 + self._transform._matrix[2]**2)
  
  def getHeight(self):
    """
    Returns the height of the rectangle.
    """
    return _math.sqrt(self._transform._matrix[1]**2 + self._transform._matrix[3]**2)

  def setWidth(self, w):
    """
    Sets the width of the rectangle to w.
    """
    if not isinstance(w, (int,float)):
      raise TypeError, 'Width must be a positive number'
    if w <= 0:
      raise ValueError, "The rectangle's width must be positive"
    factor = float(w) / self.getWidth()
    p = self._localToGlobal(self._reference)
    trans = Transformation((1.,0.,0.,1.)+p.get())
    sca = Transformation((factor,0.,0.,1.,0.,0.))
    
    self._transform = self._transform * Transformation((factor,0.,0.,1.,0.,0.))
    self._transform = trans*(sca*(trans.inv()*self._transform))
    self._objectChanged()
    
  def setHeight(self, h):
    """
    Sets the height of the rectangle to h.
    """
    if not isinstance(h, (int,float)):
      raise TypeError, 'Height must be a positive number'
    if h <= 0:
      raise ValueError, "The rectangle's height must be positive"
    factor = float(h) / self.getHeight()
    p = self._localToGlobal(self._reference)
    trans = Transformation((1.,0.,0.,1.)+p.get())
    sca = Transformation((1.,0.,0.,factor,0.,0.))
    
    self._transform = trans*(sca*(trans.inv()*self._transform))
    self._objectChanged()

  def _draw(self):
    self._beginDraw()

    _graphicsManager.addCommandToQueue(('draw rectangle', self))
    FillableShape._draw(self)
      
    self._completeDraw()

class Square(Rectangle):
  """
  A square that can be drawn to the canvas.
  """
  def __init__(self, size=10, center=None):
    """
    Construct a new instance of a Square.

    The reference point for a square is its center.

    size    the dimension of the square.  (Defaults to 10)
    center    a Point representing the placement of the rectangle's center
          (Defaults to Point(0,0) )
    """
    if not isinstance(size, (int,float)):
      raise TypeError, 'size must be a number'
    if size <= 0:
      raise ValueError, "The size must be positive."
    if center and not isinstance(center,Point):
      raise TypeError, 'center must be specified as a Point'

    Rectangle.__init__(self, size, size, center)


  def getSize(self):
    """
    Returns the length of a side of the square.
    """
    return self.getWidth()

  def setSize(self, size):
    """
    Set the length and width of the square to size.
    """
    if not isinstance(size, (int,float)):
      raise TypeError, 'size must be a number'
    if size <= 0:
      raise ValueError, "The size must be positive."
    
    Rectangle.setWidth(self, size)
    Rectangle.setHeight(self, size)

  def setWidth(self, width):
    """
    Sets the width and height of the square to given width.
    """
    if not isinstance(width, (int,float)):
      raise TypeError, 'width must be a positive number'
    if width <= 0:
      raise ValueError, "The square's width must be positive"
    self.setSize(width)

  def setHeight(self, height):
    """
    Sets the width and height of the square to given height.
    """
    if not isinstance(height, (int,float)):
      raise TypeError, 'height must be a positive number'
    if height <= 0:
      raise ValueError, "The square's height must be positive"
    self.setSize(height)

class Path(Shape):
  """
  A path that can be drawn to a canvas.
  """
  def __init__(self, *points):
    """
    Construct a new instance of a Path.

    The path is described as a series of points which are connected in order.

    These points can be initialized either be sending a single
    tuple of Point instances, or by sending each individual Point
    as a separate parameter.  (by default, path will have zero
    points)

    By default, the reference point for a path is aligned with the
    first point of the path.
    """
    Shape.__init__(self)

    if len(points)==1 and isinstance(points[0],tuple):
      points = points[0]
    for p in points:
      if not isinstance(p,Point):
        raise TypeError, 'all parameters must be Point instances'
    self._points = list(points)
    if len(self._points)>=1:
      self.adjustReference(self._points[0].getX(), self._points[0].getY())

  def addPoint(self, point):
    """
    Add a new point to the end of a Path.
    """
    if not isinstance(point,Point):
      raise TypeError, 'parameter must be a Point instance'
    self._points.append(point)
    if len(self._points)==1:  # first point added
      self._reference = Point(point.getX(), point.getY())
    self._objectChanged()

  def deletePoint(self, index):
    """
    Remove the Point at the given index.
    """
    if not isinstance(index,int):
      raise TypeError, 'index must be an integer'
    try:
      self._points.pop(index)
    except:
      raise IndexError, 'index out of range'
    self._objectChanged()

  def clearPoints(self):
    """
    Remove all points, setting this back to an empty Path.
    """
    self._points = list()
    self._objectChanged()

  def getNumberOfPoints(self):
    """
    Return the current number of points.
    """
    return len(self._points)

  def getPoint(self, index):
    """
    Return a copy of the Point at the given index.

    Subsequently mutating that copy has no effect on path.
    """
    if not isinstance(index,int):
      raise TypeError, 'index must be an integer'
    try:
      p = self._points[index]
    except:
      raise IndexError, 'index out of range'
    return Point(p.getX(), p.getY())

  def setPoint(self, index, point):
    """
    Change the Point at the given index to a new value.
    """
    if not isinstance(index,int):
      raise TypeError, 'index must be an integer'
    if not isinstance(point,Point):
      raise TypeError, 'parameter must be a Point instance'
    try:
      self._points[index] = point
    except:
      raise IndexError, 'index out of range'
    self._objectChanged()

  def getPoints(self):
    return self._points
    
  def _draw(self):
    self._beginDraw()

    _graphicsManager.addCommandToQueue(("draw path", self))
    Shape._draw(self)

    self._completeDraw()


class Polygon(Path,FillableShape):
  """
  A polygon that can be drawn to a canvas.
  """
  def __init__(self, *points):
    """
    Construct a new instance of a Polygon.

    The polygon is described as a series of points which are connected in order.
    The last point is automatically connected back to the first to close the polygon.
    
    These points can be initialized either be sending a single
    tuple of Point instances, or by sending each individual Point
    as a separate parameter.  (by default, polygon will have zero
    points)

    By default, the reference point for a polygon is aligned with
    the first point of the polygon.
    """
    FillableShape.__init__(self)
    Path.__init__(self, points)

  def _draw(self):
    self._beginDraw()

    _graphicsManager.addCommandToQueue(("draw polygon", self))
    FillableShape.draw(self)

    self._completeDraw()

class Image(Drawable):
  def __init__(self, filename):
    Drawable.__init__(self)
    if not isinstance(filename,str):
      raise TypeError, 'filename must be a string'
    self._filename = filename   # of course, we won't know if this is legitimate until it is added to a canvas
         
  def rotate(self,angle):
    """
    Not yet implemented.
    """
    raise NotImplementedError,'rotating image is not yet implemented'
    
  def scale(self,factor):
    """
    Not yet implemented.
    """
    raise NotImplementedError,'scaling image is not yet implemented'

  def draw(self):
    self._beginDraw()

    _graphicsManager.addCommandToQueue(("draw image", self))
    
    self._completeDraw()

class Text(Drawable):
  """
  A piece of text that can be drawn to a canvas.
  """
  def __init__(self, message='', size=12):
    """
    Construct a new Text instance.

    The text color is black, though this can be changed by setColor.
    The reference point for text is the upper-left hand corner of the text.

    message   a string which is to be displayed (empty string by default)
    size    the font size (12 by default)
    """
    if not isinstance(message,str):
      raise TypeError, 'message must be a string'
    if not isinstance(size,int):
      raise TypeError, 'size must be an integer'

    Drawable.__init__(self)
    self._text = message
    self._size = size
    self._color = Color("black")

  def setMessage(self, message):
    """
    Set the string to be displayed.

    message  a string
    """
    if not isinstance(message,str):
      raise TypeError, 'message must be a string'
    self._text = message
    self._objectChanged()

  def getMessage(self):
    """
    Returns the current string.
    """
    return self._text

  def setFontColor(self, color):
    """
    Set the color of the font.

    The parameter can be either:
       - a string with the name of the color
       - an (r,g,b) tuple
       - an existing Color instance
    """
    if isinstance(color,Color):
      self._color = color
    else:
      try:
        self._color = Color(color)
      except TypeError,te:
        raise TypeError,str(te)
      except ValueError,ve:
        raise ValueError,str(ve)
    self._objectChanged()

  def getFontColor(self):
    """
    Returns the current font color.
    """
    return self._color

  def setFontSize(self, fontsize):
    """
    Set the font size.
    """
    if not isinstance(fontsize,int):
      raise TypeError, 'fontsize must be an integer'
    if fontsize<=0:
      raise ValueError, 'fontsize must be positive'
    self._size = fontsize
    self._objectChanged()

  def getFontSize(self):
    """
    Returns the current font size.
    """
    return size

  def rotate(self,angle):
    """
    Not yet implemented.
    """
    raise NotImplementedError,'rotating text is not yet implemented'
    
  def scale(self,factor):
    """
    Not yet implemented.
    """
    raise NotImplementedError,'scaling text is not yet implemented.  Use setSize to change font'
 
  def getDimensions(self):
    return 20,20
 
  def _draw(self):
    self._beginDraw()

    _graphicsManager.addCommandToQueue(("draw text", self))
    
    self._completeDraw()

  # Compatibilities to previous version
  setSize = setFontSize
  getSize = getFontSize
  setColor = setFontColor
  getColor = getFontColor
  setText = setMessage
  getText = getMessage

class Button(Text, Rectangle, EventHandler):
  def __init__(self, message="", center=None):
    Text.__init__(self, message)
    w, h = self.getDimensions()
    Rectangle.__init__(self, w, h, center)
    EventHandler.__init__(self)
    self._baseBorderWidth = self._borderWidth

    self.setFillColor("white")
    self.addHandler(self)

  def handle(self, event):
    if _debug >= 3:
      print "Button self handler"
    if event._eventType == "mouse click":
      Rectangle.setBorderWidth(self, self._baseBorderWidth + 2)
    elif event._eventType == "mouse release":
      Rectangle.setBorderWidth(self, self._baseBorderWidth)

  def _draw(self):
    self._beginDraw()
    Rectangle._draw(self)
    Text._draw(self)
    self._completeDraw()

  def setBorderWidth(self, width):
    self._baseBorderWidth = width
    Rectangle.setBorderWidth(self, width)


try:
  import Tkinter as _Tkinter

  _tkroot = None

  _underlyingLibrary = 'Tkinter'

  class _TkGraphicsManager(_GraphicsManager):
    def run(self):
      global _tkroot
      if _debug >= 2: print "Starting _TkGraphicsManager instance"
      if _tkroot == None:
        _tkroot = _Tkinter.Tk()
        _tkroot.withdraw()
      _GraphicsManager.run(self)
      _tkroot.mainloop()
  
    def stop(self):
      _GraphicsManager.stop(self)
      _tkroot.quit()
  
    def _periodicCall(self):
      self.processCommands()
      if self._running:
        _tkroot.after(10, self._periodicCall)

    def removeUnderlying(self, chain):
      if _debug >= 2:
        print "Removing underlying object", chain
      chain[0][0]._canvas._canvas.delete(self._underlyingObject[chain]._object)
      self._underlyingObject.pop(chain)
      
    
      
  _UnderlyingManager = _TkGraphicsManager

  class _RenderedCanvas(object):
    def __init__(self, canvas, w, h, background, title, refresh):
      if _debug >= 2: print "Creating _RenderedCanvas"
      self._parent = canvas
      
      self._tkWin = _Tkinter.Toplevel()
      self._tkWin.protocol("WM_DELETE_WINDOW", self._parent.close)
      self._tkWin.title(title)
      self._canvas = _Tkinter.Canvas(self._tkWin,width=w,height=h,background=getTkColor(background))
      self._canvas.pack(expand=False,side=_Tkinter.TOP)
      self._tkWin.resizable(0,0)

      # Setup function to deal with events
      callback = lambda event : self._handleEvent(event)
      self._canvas.bind('<Button>', callback)
      self._canvas.bind('<ButtonRelease>', callback)
      self._canvas.bind('<Key>', callback)
      self._canvas.bind('<Motion>', callback)
      self._canvas.bind('<Enter>', callback)
      self._canvas.focus_set()
  
    def setBackgroundColor(self, color):
      self._canvas.config(background=getTkColor(color))
  
    def setWidth(self, w):
      self._canvas.config(width=w)
  
    def setHeight(self, h):
      self._canvas.config(height=h)
  
    def setTitle(self, title):
      self._tkWin.title(title)

    def open(self):
      """
      Open the canvas window (if not already open).
      """
      self._tkWin.deiconify()

    def close(self):
      """
      Close the canvas window (if not already closed).
      """
      self._tkWin.withdraw()

    def saveToFile(self, filename):
      parent = self._parent
      background = Rectangle(parent.getWidth()+2, parent.getHeight()+2)
      background.move( float(parent.getWidth())/2, float(parent.getHeight())/2 )
      background.setFillColor(parent.getBackgroundColor())
      background.setBorderColor(parent.getBackgroundColor())

      maxDepth = 0
      for o in parent._contents:
        if o.getDepth() > maxDepth:
          maxDepth = o.getDepth()

      background.setDepth(maxDepth+1)
      parent.add(background)
      self._parent.refresh(True)
      self._canvas.postscript(file=filename)
      import time
      time.sleep(3)
      parent.remove(background)

    def _handleEvent(self, event):
      global _graphicsManager
      if _debug >= 3:
        print "Event happened", self, event.type, event.x, event.y, event.char
        print "Overlapping:", self._canvas.find_overlapping(event.x, event.y, event.x, event.y)
        
      # Create the event
      e = Event()
      if not _graphicsManager._mousePrevPosition:
        e._prevx, e._prevy = event.x, event.y
      else:
        e._prevx, e._prevy = _graphicsManager._mousePrevPosition[0], _graphicsManager._mousePrevPosition[1]
      _graphicsManager._mousePrevPosition = (int(event.x), int(event.y))
      e._x, e._y = event.x, event.y
      
      if int(event.type) == 2:   # Keypress
        e._eventType = 'keyboard'
        e._key = str(event.char)
      elif int(event.type) == 4: # Mouse click
        e._eventType = 'mouse click'
        _graphicsManager._mouseButtonDown = True
      elif int(event.type) == 5: # Mouse release
        e._eventType = 'mouse release'
        _graphicsManager._mouseButtonDown = False
      elif int(event.type) == 6: # Mouse move
        if _graphicsManager._mouseButtonDown:
          e._eventType = 'mouse drag'
        else:
          return
      else:
        return
        
      if _debug >= 2:
        print "Event triggered", e._eventType, e._x, e._y, e._prevx, e._prevy, e._key
        
      # Find the shape where the event occurred:
      tkIds = self._canvas.find_overlapping(event.x, event.y, event.x, event.y)
      chain = ((self._parent, None), )
      if len(tkIds) > 0:
        for c in _graphicsManager._renderOrder[self._parent]:
          if _graphicsManager._underlyingObject.has_key(c) and _graphicsManager._underlyingObject[c]._object == tkIds[-1]:
            chain = c
        
      # Trigger the event handler(s)
      for i in range(len(chain),0,-1):
        subchain = chain[:i]
        p = _graphicsManager._transforms.get(subchain, Transformation()).image(Point(event.x, event.y))
        e.x, e.y = p._x, p._y
          
        triggered = _graphicsManager.triggerHandler(subchain[-1][0], e)
          
        if triggered:
          break
      
  def getTkColor(color):
    if color._transparent:
      return ""
    return "#%04X%04X%04X" % (256*color.getColorValue()[0], 256*color.getColorValue()[1], 256*color.getColorValue()[2])
  
  class _RenderedDrawable(object):
    def __init__(self, drawable, canvas):
      self._drawable = drawable
      self._canvas = canvas
      self._object = None
  
    def update(self, transform):
      # Fix the depth
      self._canvas._canvas._canvas.tkraise(self._object)
    
    def remove(self, doRefresh=True):
      self._canvas._canvas.remove(self, doRefresh)
  
  class _RenderedShape(_RenderedDrawable):
    def __init__(self, drawable, canvas):
      _RenderedDrawable.__init__(self, drawable, canvas)

    def update(self, transform):
      _RenderedDrawable.update(self, transform)
      # cannot update border color because it is called 'outline' for fillables, yet 'fill' for path/line
      self._canvas._canvas._canvas.itemconfigure(self._object, width=self._drawable._borderWidth)
  
  class _RenderedFillableShape(_RenderedShape):
    def __init__(self, drawable, canvas):
      _RenderedShape.__init__(self, drawable, canvas)
  
    def update(self, transform):
      _RenderedShape.update(self, transform)
      self._canvas._canvas._canvas.itemconfigure(self._object, fill=getTkColor(self._drawable._fillColor), outline=getTkColor(self._drawable._borderColor))

  class _RenderedCircle(_RenderedFillableShape):
    def __init__(self, drawable, canvas, transform):
      _RenderedFillableShape.__init__(self, drawable, canvas)
      center = transform.image(Point(0.,0.))
      radius = _math.sqrt(abs(transform.det()))
      self._object = canvas._canvas._canvas.create_oval(center.getX() - radius, center.getY() - radius,
                                center.getX() + radius, center.getY() + radius,
                                fill=getTkColor(self._drawable._fillColor),
                                outline=getTkColor(self._drawable._borderColor),
                                width=self._drawable._borderWidth)
      _RenderedDrawable.update(self, transform)
  
    def update(self, transform):
      # Update interior and border
      _RenderedFillableShape.update(self, transform)
      
      # Update size and position
      center = transform.image(Point(0.,0.))
      radius = _math.sqrt(abs(transform.det()))

      self._canvas._canvas._canvas.coords(self._object, center.getX() - radius, center.getY() - radius, center.getX() + radius, center.getY() + radius)
      _RenderedDrawable.update(self, transform)


  class _RenderedRectangle(_RenderedFillableShape):
    def __init__(self, drawable, canvas, transform):
      _RenderedFillableShape.__init__(self, drawable, canvas)
      points = [Point(-.5,-.5), Point(-.5,.5), Point(.5,.5), Point(.5,-.5)]
      for i in range(4):
        points[i] = transform.image(points[i])
      self._object = canvas._canvas._canvas.create_polygon(points[0].get(), points[1].get(), points[2].get(), points[3].get(),
                                fill=getTkColor(self._drawable._fillColor),
                                outline=getTkColor(self._drawable._borderColor),
                                width=self._drawable._borderWidth)
      _RenderedDrawable.update(self, transform)

    def update(self, transform):
      _RenderedFillableShape.update(self, transform)
      points = [Point(-.5,-.5), Point(-.5,.5), Point(.5,.5), Point(.5,-.5)]
      for i in range(4):
        points[i] = transform.image(points[i])
      self._canvas._canvas._canvas.coords(self._object, points[0].getX(), points[0].getY(), points[1].getX(), points[1].getY(),
                        points[2].getX(), points[2].getY(), points[3].getX(), points[3].getY())

  class _RenderedPath(_RenderedShape):
    def __init__(self, drawable, canvas, transform, points):
      _RenderedShape.__init__(self, drawable, canvas)

      statement = "self._object = canvas._canvas._canvas.create_line("
      for p in points:
        statement += str(transform.image(p).getX()) + ", " + str(transform.image(p).getY()) + ", "
      statement += "fill=getTkColor(self._drawable._borderColor), width=self._drawable._borderWidth)"
      exec statement
      _RenderedDrawable.update(self, transform)

    def update(self, transform):
      _RenderedShape.update(self, transform)
      self._canvas._canvas._canvas.itemconfigure(self._object, fill=getTkColor(self._drawable._borderColor))

      statement = "self._canvas._canvas._canvas.coords(self._object"
      for p in self._drawable.getPoints():
        statement += ", " + str(transform.image(p).getX()) + ", " + str(transform.image(p).getY())
      statement += ")"
      exec statement

  class _RenderedPolygon(_RenderedFillableShape):
    def __init__(self, drawable, canvas, transform, points):
      _RenderedFillableShape.__init__(self, drawable, canvas)

      statement = "self._object = canvas._canvas._canvas.create_polygon("
      for p in points:
        statement += str(transform.image(p).getX()) + ", " + str(transform.image(p).getY()) + ", "
      statement += "fill=getTkColor(self._drawable._fillColor), outline=getTkColor(self._drawable._borderColor), width=self._drawable._borderWidth)"

      exec statement
      _RenderedDrawable.update(self, transform)

    def update(self, transform):
      _RenderedFillableShape.update(self, transform)

      statement = "self._canvas._canvas._canvas.coords(self._object"
      for p in self._drawable.getPoints():
        statement += ", " + str(transform.image(p).getX()) + ", " + str(transform.image(p).getY())
      statement += ")"
      exec statement

  class _RenderedText(_RenderedDrawable):
    def __init__(self, drawable, canvas, transform):
      _RenderedDrawable.__init__(self, drawable, canvas)
      center = transform.image(Point(0.,0.))
      
      self._object = canvas._canvas._canvas.create_text(center.get(), text=drawable._text, anchor='center',
              fill=getTkColor(drawable._color), font=('Helvetica', drawable._size, 'normal') )
      _RenderedDrawable.update(self, transform)
  
    def update(self, transform):
      # Update interior and border
      _RenderedDrawable.update(self, transform)
      
      # Update size and position
      center = transform.image(Point(0.,0.))

      self._canvas._canvas._canvas.coords(self._object, center.getX(), center.getY())
      self._canvas._canvas._canvas.itemconfigure(self._object, font=('Helvetica', self._drawable._size, 'normal'), fill=getTkColor(self._drawable._color), text=self._drawable._text)


except ImportError:
  pass
    
    
