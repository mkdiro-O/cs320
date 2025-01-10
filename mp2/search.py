class Node():
    def __init__(self, key):
        self.key = key
        self.values = []
        self.left = None
        self.right = None
        
    def __len__(self):
        size = len(self.values)
        if self.left is not None:
            size += len(self.left)
        if self.right is not None:
            size += len(self.right)  
        return size
    
    def lookup(self, key):
        if key == self.key:
            return self.values
        elif key < self.key and self.left != None:
            return self.left.lookup(key)
        elif key > self.key and self.right != None:
            return self.right.lookup(key)
        else:
            return []
        
class BST():
    def __init__(self):
        self.root = None
        
    def __dump(self, node):
        if node == None:
            return
        self.__dump(node.left)
        print(node.key, ":", node.values)
        self.__dump(node.right) 
        
    def __getitem__(self, key):
        if self.root != None:
            return self.root.lookup(key)
        else:
            return []

    def dump(self):
        self.__dump(self.root)

    def add(self, key, val):
        if self.root == None:
            self.root = Node(key)

        curr = self.root
        while True:
            if key < curr.key:
                # go left
                if curr.left == None:
                    curr.left = Node(key)
                curr = curr.left
            elif key > curr.key:
                # go right
                if curr.right == None:
                    curr.right = Node(key)
                curr = curr.right
            else:
                # found it!
                assert curr.key == key
                break

        curr.values.append(val)
    
    def get_height(self, node):
        if node == None:
            return 1
        
        left_height = self.get_height(node.left)    
        right_height = self.get_height(node.right)
            
        return max(left_height, right_height) + 1
    
    
    def num_nodes(self, node=None):
        if self.root is None:
            return 0
    
        stack = [self.root]
        count = 0

        while stack:
            node = stack.pop()
            count += 1

            if node.left is not None:
                stack.append(node.left)
            if node.right is not None:
                stack.append(node.right)
    
        return count
    
    def num_nonleaf_nodes(self, node=None):
        if node is None:
            node = self.root

        if node is None or (node.left is None and node.right is None):
            return 0

        left_nonleaf_nodes = self.num_nonleaf_nodes(node.left) if node.left else 0
        right_nonleaf_nodes = self.num_nonleaf_nodes(node.right) if node.right else 0

        return 1 + left_nonleaf_nodes + right_nonleaf_nodes

        return 1 + left_nonleaf_nodes + right_nonleaf_nodes

    def num_leaf_nodes(self):
        total_nodes = self.num_nodes()
        non_leaf_nodes = self.num_nonleaf_nodes()
        return total_nodes - non_leaf_nodes
    
    def find_keys(self, n):
        stack = []
        visited = []

        current = self.root
        while current or stack:
            while current:
                stack.append(current)
                current = current.right

            current = stack.pop()
            visited.append(current.key)
            if len(visited) == n:
                break

            current = current.left

        return visited[-1] if len(visited) > 0 else None
    