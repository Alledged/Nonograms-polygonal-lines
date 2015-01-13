from BinarySearchTree import BinarySearchTree as _BinarySearchTree

_DEBUG = 0

def _identifyNephews(sibling, parent):
    if sibling == parent.getLeft():
        return sibling.getRight(),sibling.getLeft()
    else:
        return sibling.getLeft(),sibling.getRight()


class RedBlackTree(_BinarySearchTree):
    """A red-black tree for storing arbitrary (key,data) pairs.

    This particular implementation relies upon storing all data at
    leaves of the tree rather than at internal nodes.

    Entries with equal keys will be stored consolidated at a single leaf.
    """

    #####################################################################
    class _Node(_BinarySearchTree._Node):
        """Structure for single node of tree.

        Each node has a key, a left child and a right child.

        Data is stored at leaves and as complete hack, we designate
        this by having left and right pointers equal, and pointing to
        the data.
        """
        def __init__(self, key=None):
            """Creates a leaf with no data entries.

            key is None if not otherwise specified.
            color is initially black.
            """
            _BinarySearchTree._Node.__init__(self,key)   # parent constructor
            self._black = True

        def isBlack(self):
            return self._black

        def isRed(self):
            return not self._black

        def setBlack(self,yes=True):
            self._black = yes

        def __str__(self):
            if self._black:
                color = 'black'
            else:
                color = 'red'
            return _BinarySearchTree._Node.__str__(self) + " and color %s"%color
        
    #####################################################################

    
    def _fixupInsert(self, path):
        path.pop()                    # end should be a leaf (black by default)
        if path:
            path[-1].setBlack(False)  # this presumed new internal should be set to red
            good = False
            while not good:
                good = True               # generally the case
                if len(path) == 1:
                    path[-1].setBlack()   # root should be black
                else:
                    parent = path[-2]
                    if parent.isRed():
                        grandparent = path[-3]   # must exist, since root is never red
                        uncle = grandparent.getOtherChild(parent)
                        if uncle.isBlack():
                            if _DEBUG>1: print "misshapen 4-node"
                            # poorly shaped 4-node
                            if (grandparent.getLeft() == parent) != (parent.getLeft() == path[-1]):
                                # crooked alignment requires extra rotation
                                if _DEBUG>1: print "extra rotate"
                                self._rotate(path[-1],parent,grandparent)
                                path[-2:] = [path[-1], path[-2]]  # invert last two entries
                                if _DEBUG>1: print "extra rotate"
                            # in either case, need to rotate parent with grandparent
                            grandparent.setBlack(False)
                            path[-2].setBlack(True)
                            path[-1].setBlack(False)
                            if len(path)==3:
                                if _DEBUG>1: print "rotate (no grandparent)"
                                self._rotate(path[-2],path[-3])
                            else:
                                if _DEBUG>1: print "rotate"
                                self._rotate(path[-2],path[-3],path[-4])
                        else:
                            # 5-node must be recolored
                            if _DEBUG>1: print "recoloring 5-node"
                            parent.setBlack()
                            uncle.setBlack()
                            grandparent.setBlack(False)
                            # continue from grandparent
                            path.pop()
                            path.pop()
                            good = False

        if _DEBUG>0 and self._validate() == -1:
            print 'Error after insertion.'


    def _removeLeaf(self, path):
        """Last node of path is a leaf that should be removed."""
        problem = len(path) >= 2 and path[-2].isBlack()
        _BinarySearchTree._contractAbove(self,path)        # path is updated automatically
        while problem:
            problem = False  # typically, we fix it. We'll reset to True when necessary
            if path[-1].isRed():
                path[-1].setBlack()   # problem solved
            elif len(path) >= 2:
                # bottom node is a "double-black" that must be remedied
                if _DEBUG>1: print "double-black node must be resolved:",path[-1]
                parent = path[-2]
                sibling = parent.getOtherChild(path[-1])
                if len(path) >= 3:
                    grandparent = path[-3]
                else:
                    grandparent = None
                    
                if sibling.isRed():
                    # our parent is a 3-node that we prefer to realign
                    if _DEBUG>1: print "realigning red sibling"
                    sibling.setBlack(True)
                    parent.setBlack(False)
                    self._rotate(sibling,parent,grandparent)
                    path.insert(-2,sibling)   # reflects the rotation of sibling above parent
                    grandparent = sibling
                    sibling = parent.getOtherChild(path[-1])  # will surely be black this time

                # now sibling is black
                nephewA,nephewB = _identifyNephews(sibling,parent)   # closer,farther
                if _DEBUG>1: print "nephews:",nephewA,"-",nephewB
                if nephewA.isBlack() and nephewB.isBlack():
                    # we and sibling are 2-nodes.  Recolor sibling to enact merge
                    if _DEBUG>1: print "sibling also 2-node; recoloring"
                    sibling.setBlack(False)
                    if parent.isRed():
                        parent.setBlack()
                    else:
                        if _DEBUG>1: print "will continue with",path[-1]
                        path.pop()
                        problem = True   # must continue from parent level
                else:
                    # should be able to maneuver to borrow from sibling
                    if not nephewA.isRed():
                        # rotate other nephew and sibling
                        if _DEBUG>1: print "realigning nephews"
                        self._rotate(nephewB,sibling,parent)
                        nephewB.setBlack(True)
                        sibling.setBlack(False)
                        sibling = nephewB
                        nephewA,nephewB = _identifyNephews(sibling,parent)
                        if _DEBUG>1: print "nephews:",nephewA,"-",nephewB

                    # at this point, nephewA is guaranteed to be red. Let's borrow from it
                    self._rotate(nephewA,sibling,parent)
                    self._rotate(nephewA,parent,grandparent)
                    nephewA.setBlack(parent.isBlack())   # they've been promoted
                    parent.setBlack()
                    # cross your fingers; should be done!

        if _DEBUG>0 and self._validate() == -1:
            print 'Error after deletion.'

    def _validate(self,here=None,prevBlack=True):
        """Returns the black depth if valid;  -1 if invalid."""
        if here is None:
            here = self._root
        if here is None:
            answer =  0
        elif here.isExternal():
            if here.isRed():
                answer = -1
            else:
                answer =  1
        else:
            if here.isRed() and not prevBlack:
                answer = -1   # should not have two reds in a row
            else:
                leftDepth = self._validate(here.getLeft(),here.isBlack())
                rightDepth = self._validate(here.getRight(),here.isBlack())
                if leftDepth == -1 or rightDepth == -1 or leftDepth != rightDepth:
                    answer = -1
                else:
                    if here.isBlack():
                        answer = 1 + leftDepth
                    else:
                        answer = leftDepth
        return answer
    
if __name__ == '__main__':
    from BinarySearchTree import _test
    _test(RedBlackTree(),10000,_DEBUG)
    
