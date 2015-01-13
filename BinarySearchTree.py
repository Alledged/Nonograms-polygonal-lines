class BinarySearchTree:
    """A generic binary search tree for storing arbitrary (key,data) pairs.

    This particular implementation relies upon storing all data at
    leaves of the tree rather than at internal nodes.  At all times it
    guarantees that an internal node's key is precisely that of the
    rightmost leaf in the left subtree.

    Entries with equal keys will be stored consolidated at a single leaf.
    """

    #####################################################################
    class _Node:
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
            self._key = key
            self._left = self._right = []

        def isInternal(self):
            return self._left is not self._right

        def isExternal(self):
            return self._left is self._right
        
        def getKey(self):
            return self._key

        def setKey(self, key):
            self._key = key

        def getLeft(self):
            return self._left

        def setLeft(self, node):
            if not isinstance(node,self.__class__):
                raise TypeError('left must be a _Node instance')
            self._left = node

        def getRight(self):
            return self._right

        def setRight(self, node):
            if not isinstance(node,self.__class__):
                raise TypeError('right must be a _Node instance')
            self._right = node

        def getData(self):
            if not self.isExternal():
                raise ValueError('this is not an external node')
            return self._left
            
        def setData(self, data):
            self._left = self._right = data

        def getOtherChild(self, knownchild):
            """Assuming knownchild is a child, retrieves the other sibling.

            Return None if no other sibling.
            """
            if knownchild == self._left:
                return self._right
            else:
                return self._left

        def __str__(self):
            if self.isInternal():
                return 'Internal with key %s'%str(self._key)
            else:
                return 'External with key %s'%str(self._key)
            
    #####################################################################
    class _Key:
        pass

    _minKey = _Key()
    _maxKey = _Key()
    #####################################################################

    
    def __init__(self,cmp=cmp):
        """Creates a new (empty) BinarySearchTree.

        cmp   A callable comparator for keys (default: built-in cmp)

              During searches, the implementation guarantees that the
              search key is the first of the two parameters sent to
              comparator.
        """
        self._cmp = cmp
        self._size = 0
        self._root = None

    def __len__(self):
        """Returns number of (key,data) entries within the collection."""
        return self._size

    def __contains__(self, key):
        if self:
            path = self._tracePath(key)
            return 0 == self._cmp(key,path[-1].getKey())
        else:
            return False

    def find(self, key):
        """Returns an example of an entry with given key.

        raises KeyError if none found.
        """
        if self:
            path = self._tracePath(key)
            if 0 == self._cmp(key,path[-1].getKey()):
                return path[-1].getData()[0]
        raise KeyError('key not found: '+str(key))

    def findAll(self, key, node=None):
        """Returns a list of (key,data) tuples for entries that match the given key."""
        results = []
        if self:
            if node is None:
                node = self._root
            cmp = self._cmp(key,node.getKey())
            if node.isExternal():
                if cmp == 0:
                    results.extend([(node.getKey(),x) for x in node.getData()])
            else:
                results.extend(self.findAll(key,node.getLeft()))
                results.extend(self.findAll(key,node.getRight()))
        return results

    def findLow(self, key):
        """Returns a (key,data) tuple with nearest key less than or equal to given key.

        Returns None when there is no such entry.
        """
        path = self._tracePath(key)
        while path and self._cmp(key,path[-1].getKey()) < 0:
            path.pop()   # back up if necessary
        if path:
            # found ancestor of the desired node
            walk = path[-1]
            if walk.isInternal():
                walk = walk.getLeft()
            while walk.isInternal():
                walk = walk.getRight()
            return (walk.getKey(),walk.getData()[0])
        else:
            return None

    def findHigh(self, key):
        """Returns a (key,data) tuple with nearest key less than or equal to given key.

        Returns None when there is no such entry.
        """
        path = self._tracePath(key)
        while path and self._cmp(key,path[-1].getKey()) > 0:
            path.pop()   # back up if necessary
        if path:
            # found ancestor of the desired node
            walk = path[-1]
            if walk.isInternal():
                walk = walk.getRight()
            while walk.isInternal():
                walk = walk.getLeft()
            return (walk.getKey(),walk.getData()[0])
        else:
            return None


    def findMin(self):
        """Returns (key,data) tuple for the minimum element currently in tree.

        In case of a tie, an arbitrary data element is selected.
        """
        if self:
            path = self._tracePath(BinarySearchTree._minKey)
            return (path[-1].getKey(), path[-1].getData()[-1])
        else:
            raise RuntimeError('tree is empty')

    def findMax(self):
        """Returns (key,data) tuple for the maximum element currently in tree.

        In case of a tie, an arbitrary data element is selected.
        """
        if self:
            path = self._tracePath(BinarySearchTree._maxKey)
            return (path[-1].getKey(), path[-1].getData()[-1])
        else:
            raise RuntimeError('tree is empty')

    def _fixupInsert(self, path):
        """Only called when the end of the path is a newly created node."""
        pass

    def insert(self, key, data=None):
        """Inserts a new element with given key and data."""
        if self:
            path = self._tracePath(key)
            end = path[-1]
            case = self._cmp(key, end.getKey())
            if case == 0:                      # existing key
                end.getData().append(data)
            else:
                clone = self._Node(end.getKey())
                clone.setData(end.getData())
                newleaf = self._Node(key)
                newleaf.setData([data])
                path.append(newleaf)
                if case == -1:                 # new item is to left
                    end.setKey(key)
                    end.setLeft(newleaf)
                    end.setRight(clone)
                else:
                    # existing key is fine
                    end.setLeft(clone)
                    end.setRight(newleaf)
                self._fixupInsert(path)
        else:
            self._root = self._Node(key)
            self._root.setData([data])
            path = [self._root]
            self._fixupInsert(path)
        self._size += 1


    def _remove(self, key, all=False):
        """Internal version.

        Returns three things.  The first is a list of data (empty if
        no match, and single element when 'all' is False).  The second
        is the matching key.  The third piece is the path that exists
        AFTER the removal.
        """
        path = []
        results = []
        matchingKey = None
        if self:
            path = self._tracePath(key)
            end = path[-1]
            if key is BinarySearchTree._minKey or \
               key is BinarySearchTree._maxKey or \
               self._cmp(key,end.getKey()) == 0:
                matchingKey = end.getKey()
                matches = end.getData()
                if not all and len(matches) > 1:
                    results = [matches.pop()]
                else:
                    # the real case.  This node must disappear
                    results = matches

                    if len(path) > 1:
                        # get rid of this key from internal nodes, replacing with sibling's key
                        if path[-1] is path[-2].getLeft():
                            replacementKey = path[-2].getRight().getKey()
                        else:
                            temp = path[-2].getLeft()
                            while temp.isInternal():
                                temp = temp.getRight()
                            replacementKey = temp.getKey()
                        
                        for node in path:
                            if node.getKey() == path[-1].getKey():
                                node.setKey(replacementKey)

                    # now get rid of the leaf itself
                    self._removeLeaf(path)
                    
        self._size -= len(results)
        return results,matchingKey,path
    

    def remove(self, key):
        """Removes and returns arbitrary data value associated with given key.

        Raises KeyError if not found.
        """
        results,foundkey,path = self._remove(key)
        if len(results) == 0:
            raise KeyError('key not found: '+str(key))
        else:
            return results[-1]   # should presumably be the only one

    def removeAll(self, key):
        """Removes and returns list of all data values associated with given key.

        Raises KeyError if not found.
        """
        results,foundkey,path = self._remove(key,True)
        if len(results) == 0:
            raise KeyError('key not found: '+str(key))
        else:
            return results

    def removeMin(self):
        """Removes and returns arbitrary (key,data) pair associated with minimum key.

        Raises RuntimeError if tree empty.
        """
        if self:
            results,foundkey,path = self._remove(BinarySearchTree._minKey)
            return (foundkey,results[0])
        else:
            raise RuntimeError('tree is empty')

    def removeMax(self):
        """Removes and returns arbitrary (key,data) pair associated with maximum key.

        Raises RuntimeError if tree empty.
        """
        if self:
            results,foundkey,path = self._remove(BinarySearchTree._maxKey)
            return (foundkey,results[-1])
        else:
            raise RuntimeError('tree is empty')


    def _removeLeaf(self, path):
        """Last node on this path is a leaf that should be removed from the tree."""
        # now get rid of the node itself
        self._contractAbove(path)

    def _contractAbove(self, path):
        """Child  and parent disapear, with sibling taking place of parent.

        Updates path accordingly.
        """
        if len(path) == 1:
            self._root = None
            path.pop()
        else:
            sib = path[-2].getOtherChild(path[-1])
            if len(path) == 2:  # parent is the root
                self._root = sib
            else:
                if path[-2] == path[-3].getLeft():
                    path[-3].setLeft(sib)
                else:
                    path[-3].setRight(sib)
            path.pop()
            path.pop()
            path.append(sib)


    def _rotate(self, child, parent, grandparent=None):
        """Rotate locally so that child is promoted and parent is demoted."""
        if grandparent:
            if grandparent.getLeft() == parent:
                grandparent.setLeft(child)
            else:
                grandparent.setRight(child)
        else:
            self._root = child   # becoming the root
        if parent.getLeft() == child:
            parent.setLeft(child.getRight())
            child.setRight(parent)
        else:
            parent.setRight(child.getLeft())
            child.setLeft(parent)
                

    def _tracePath(self, key):
        """Returns the list of visited nodes from the root down to and including the leaf.

        key      if BinarySearchTree._minKey  will find minimum of all keys
                 if BinarySearchTree._maxKey  will find maximum of all keys
                 otherwise uses comparator
        """
        path = []
        if self._root:
            walk = self._root
            path.append(walk)
            while walk.isInternal():
                if key is BinarySearchTree._maxKey or \
                       (key is not BinarySearchTree._minKey and self._cmp(key,walk.getKey()) > 0):
                    walk = walk.getRight()
                else:
                    walk = walk.getLeft()
                path.append(walk)
        return path

    def processAll(self, operation, fromNode=None):
        """Visits all entries in order.
        
        Operation is assumed to be a callable object that will be sent key and data as two parameters.
        """
        if fromNode is None:
            fromNode = self._root
        if fromNode:
            if fromNode.isInternal():
                self.processAll(operation,fromNode.getLeft())
                self.processAll(operation,fromNode.getRight())
            else:
                key = fromNode.getKey()
                data = fromNode.getData()
                for d in data:
                    operation(key,d)

    def _dump(self, fromNode=None):
        """preorder dump"""
        if self._root:
            if fromNode is None:
                fromNode = self._root
            print fromNode
            if fromNode.isInternal():
                self._dump(fromNode.getLeft())
                self._dump(fromNode.getRight())

def _test(emptytree,N,_DEBUG=0):
    import random
    data = range(N) * 2
    random.shuffle(data)
    tree = emptytree
    for i in data:
        if _DEBUG>2:
            print "Dump before inserting",i
            tree._dump()
            print
        tree.insert(i)
    if len(tree) != 2 * N:
        raise RuntimeError('full tree has wrong size')

#    def printFunc(key,data):
#        print 'visiting',key
#    tree.processAll(printFunc)

    for count in range(N):
        for i in range(2):
            if _DEBUG>2:
                print "Dump before removeMin"
                tree._dump()
                print
            largest = tree.removeMax()
            if largest[0] != N-1-count:
                raise RuntimeError('entry %d reported as min, although %d expected'%(largest[0],N-1-count))
    if len(tree) != 0:
        raise RuntimeError('empty tree has wrong size')
    

if __name__ == '__main__':
    _test(BinarySearchTree(),10000)
