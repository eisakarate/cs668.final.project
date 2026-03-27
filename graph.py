from typing import Union
#-----------------------------
# edge of a graph with from and to, as well as weight
#-----------------------------
class Edge:
    def __init__ (self, from_node: int, to_node: int, weight: float, label: str = "'"):
        self.from_node: int = from_node # set origin
        self.to_node: int = to_node # store designation
        self.weight: float = weight     # store weight
        self.label: str = label # store label

    def __repr__(self):
        return f"(from_node: {self.from_node}, to_node: {self.to_node}, weight: {self.weight})"

#-----------------------------
# a node in a graph
#-----------------------------
class Node:
    def __init__ (self, index: int, label=None):
        self.index:int = index  # index of a node (assumed to be unique in the graph, usually an array index or matrix index)
        self.edges: dict = {}   # edges coming out from this node, defaults to an empty set of edges
        self.label = label # data point used to store a "visual" label used to identify a node or a state

    # total number of edges originating from this node
    def num_edges(self) -> int:
        return len(self.edges)
    
    # returns an edge from this node that connects to the specified neighbor (if it exists)
    def get_edge(self, neighbor: int) -> Union[Edge, None]:
        if neighbor in self.edges:
            return self.edges[neighbor]
        return None
    
    # add an edge or updates it
    # this is for a undirected graph (as the there is only one edge permitted per neighbor)
    def add_edge(self, neighbor: int, weight: float, edge_label: str = ""):
        self.edges[neighbor] = Edge(from_node=self.index, to_node=neighbor, weight=weight, label=edge_label)

    # removes an edge, if it exists
    def remove_edge(self, neighbor:int):
        if neighbor in self.edges:
            del self.edges[neighbor]
    
    # returns all the edges (just the Edge instances)
    def get_edge_list(self) -> list:
        return list(self.edges.values())
    
    def get_sorted_edge(self) -> list:
        result = []
        neighbors = (list)(self.edges.keys()) # get list of indexes
        neighbors.sort() # sort the indexes

        #iterate through the sorted indexes
        for n in neighbors:
            result.append(self.edges[n])

        return result
    
    # get neighbors of this node
    def get_neighbors(self) -> set:
        neighbors: set = set()

        for curEdge in self.edges.values():
            neighbors.add(curEdge.to_node)

        return neighbors
    
    # get out-neighbors for digraph
    def get_out_neighbors(self) -> set:
        neighbors: set = set()

        for curEdge in self.edges.values():
            neighbors.add(curEdge.to_node)

        return neighbors
    
#-----------------------------
# graph
#-----------------------------
class Graph:
    def __init__ (self, num_nodes: int, undirected: bool=False):
        self.num_nodes: int = num_nodes  # set the number of nodes
        self.undirected: bool = undirected

        self.nodes: list = [Node(j) for j in range(num_nodes)]  # initialize the list with nodes (w/o edges)

    def get_edge(self, from_node: int, to_node: int) -> Union[Edge, None]: #Union -> tells devs that the method return either an Edge or None
        #prevent "index not found error"
        if from_node < 0 or from_node >= self.num_nodes:
            raise IndexError
        if to_node < 0 or to_node >= self.num_nodes:
            raise IndexError
        
        #get the edge for the specified neighbor, if it exists
        return self.nodes[from_node].get_edge(to_node)
    
    # check if the nodes have an edge between them (i.e., are they neighbors?)
    def is_edge(self, from_node: int, to_node: int) -> bool:
        return self.get_edge(from_node=from_node, to_node=to_node) is not None
    
    def make_edge_list(self) -> list:
        all_edges: list = []
        for node in self.nodes:
            for edge in node.edges.values():
                all_edges.append(edge)
        return all_edges

    def insert_edge(self, from_node: int, to_node: int, weight: float, edge_label: str = ""):
        #prevent "index not found error"
        if from_node < 0 or from_node >= self.num_nodes:
            raise IndexError
        if to_node < 0 or to_node >= self.num_nodes:
            raise IndexError
        
        #add a the edge
        self.nodes[from_node].add_edge(neighbor=to_node, weight=weight, edge_label=edge_label)

        #add a "return" (i.e., corresponding return) edge if this is NOT a directed graph
        # important: weight is set to be the same
        if self.undirected:
            self.nodes[to_node].add_edge(neighbor=from_node, weight=weight, edge_label=edge_label)

    def remove_edge(self, from_node: int, to_node: int, weight: float):
        #prevent "index not found error"
        if from_node < 0 or from_node >= self.num_nodes:
            raise IndexError
        if to_node < 0 or to_node >= self.num_nodes:
            raise IndexError
        
        self.nodes[from_node].remove_edge(to_node)

        # remove the "return" (i.e., corresponding return) edge if this is NOT a directed graph
        if self.undirected:
            self.nodes[to_node].remove_edge(from_node)

    def insert_node(self, label: None) -> Node:
        new_node: Node = Node(self.num_nodes, label=label) #set the index to the length
        self.nodes.append(new_node)
        self.num_nodes += 1 # increment the node count by 1
        return new_node
    
    #creates a copy of the graph w/o referencing the original
    def make_copy(self):
        returnGraph: Graph = Graph(num_nodes=self.num_nodes, undirected=self.undirected)

        for curNode in self.nodes:
            returnGraph.nodes[curNode.index].label = curNode.label  # set the node's label, this is possible because the constructor for the graph provisions all the node instances

            # copy the edges 
            for curEdge in curNode.edges.values():
                returnGraph.insert_edge(from_node=curEdge.from_node, to_node=curEdge.to_node, weight=curEdge.weight)

        return returnGraph
    
    # get in-neighbors for a specified node
    def get_in_neighbors(self, target: int) -> set:
        neighbors: set = set()

        # iterate through the nodes
        for curNode in self.nodes:
            # check if the target node is in one of the "to-edges" of a given node
            # this works because the dictionary (edges) uses the target edge as the index
            if target in curNode.edges:
                # add the current Node's index
                neighbors.add(curNode.index)
        
        #return
        return neighbors

#-- serialization
def graph_to_dict(obj):
    # handle Graph, Node, and Edge objects (as a dictionary, 'cause it is)
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    
    # handle sets
    if isinstance(obj, set):
        return list(obj)
    
    #not supported
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

## g -> graph
## ind -> index of node of interest
def clustering_coefficient(g: Graph, ind: int) -> float:
    # get neighbors of a given node (n0)
    neighbors: set = g.nodes[ind].get_neighbors()
    cnt_neighbors = len(neighbors)

    # iterate over the neighbors
    #   for a given Neighbor (n1), get all of its edges (n1Edges)
    #       if an entry (n1Edge) is contained in (n0), then add 1
    #           to prevent double counting, count only n2 that have not been counted
    count: int = 0
    for n1 in neighbors:
        for n1Edge in g.nodes[n1].get_edge_list():
            if n1Edge.to_node > n1 and n1Edge.to_node in neighbors:
                count+= 1

    # calculate total possible (n choose 2)
    totalPossible = ((cnt_neighbors)*(cnt_neighbors-1))/2.0

    if totalPossible == 0.0:
        return 0.0 # catch for divide-by-zero (i.e., has no edges or one neighbor)
    print(f"{count}/{totalPossible}")
    return (count / totalPossible)

def average_clustering_coefficient(g: Graph) -> float:
    if g.num_nodes == 0:
        return 0.0

    totalClusteringCoefficient: float = 0.0
    for n in range(g.num_nodes):
        totalClusteringCoefficient += clustering_coefficient(g=g, ind=n)

    return (totalClusteringCoefficient) / (g.num_nodes)

## g -> graph
## ind -> index of the node of interest
## closed -> true, include source code, false, exclude source node
def generate_undirected_neighborhood_subgraph(g: Graph, ind: int, closed: bool): 
    # check if this is a directed graph
    if not g.undirected: 
        raise ValueError

    # to generate a sub-graph
    # 1. get all the neighbors
    # 2. for each Neighbor, get all the edges
    #   -> important, node index changes now.  So we need a map (index_old to index_new)
    #   -> important, this is why the nodes have a "label" to identify it
    # 1. get neighbors for a given node
    nodes_to_get_edges_for: set = g.nodes[ind].get_neighbors()
    if closed:
        nodes_to_get_edges_for.add(ind)
    #-- index map
    indexMap = {}
    #-- enumerate iterates over an iterable object then
    #--     returns an Enumerable object, a tuple of (index, element)
    #-- here, we are using the unpack feature available in Python to loop over the output
    for new_index, old_index in enumerate(nodes_to_get_edges_for):
        indexMap[old_index] = new_index
    
    # 2. generate a new graph using the nodes of interest
    subGraph: Graph = Graph(num_nodes=len(nodes_to_get_edges_for), undirected=True)
    #   loop through the edges of interest
    for curN in nodes_to_get_edges_for:
        # for each node
        # get the edges
        # add it to the graph, using the new index
        for curEdge in g.nodes[curN].get_edge_list():
            #check if the current edge is "connected" to of the nodes we are interested in
            if curEdge.to_node in nodes_to_get_edges_for:
                subGraph.insert_edge(
                    from_node=indexMap[curN], # get new index for the current node in the new graph
                    to_node=indexMap[curEdge.to_node],
                    weight=curEdge.weight
                )
    
    return subGraph

# Adjacency Matrix 
class GraphMatrix:
    def __init__(self, num_nodes: int, undirected: bool = False):
        self.num_nodes:int = num_nodes
        self.undirected:bool = undirected

        #initialize a 2-D matrix (a list of lists) of size (num_nodes), that is pre-filled with values (0.0)
        # (0.0) * num_nodes -> creates a list of length (num_nodes) with values of (0.0) 
        #   example: (0.0) * 3 -> [0.0, 0.0, 0.0]
        #
        # for _ in range(num_nodes) -> repeats the above line ((0.0 * num_nodes))
        #   (_): indicates that the loop variable, not really defined, is not used in the comprehension
        self.connections = [[0.0] * num_nodes for _ in range(num_nodes)]

    def get_edge(self, from_node: int, to_node: int) -> float: 
        #prevent "index not found error"
        if from_node < 0 or from_node >= self.num_nodes:
            raise IndexError
        if to_node < 0 or to_node >= self.num_nodes:
            raise IndexError
        
        #get the edge for the specified neighbor, if it exists
        return self.connections[from_node][to_node]
    
    def set_edge(self, from_node: int, to_node: int, weight: float):
        #prevent "index not found error"
        if from_node < 0 or from_node >= self.num_nodes:
            raise IndexError
        if to_node < 0 or to_node >= self.num_nodes:
            raise IndexError
        
        self.connections[from_node][to_node] = weight
        if self.undirected:
            self.connections[to_node][from_node] = weight
    
if __name__ =="__main__":
    print("testing")
    g:Graph = Graph(5, undirected=False)

    g.insert_edge(0, 1, 1.0)
    g.insert_edge(0, 3, 1.0)
    g.insert_edge(0, 4, 3.0)

    g.insert_edge(1, 2, 2.0)
    g.insert_edge(1, 4, 1.0)

    g.insert_edge(3, 4, 3.0)

    g.insert_edge(4, 2, 3.0)
    g.insert_edge(4, 3, 3.0)

    g2 = g.make_copy()

    print(g.nodes)
    print(g2.nodes)

    gM: GraphMatrix = GraphMatrix(5, undirected=False)
    gM.set_edge(0, 1, 1.0)
    gM.set_edge(0, 3, 1.0)
    gM.set_edge(0, 4, 3.0)

    gM.set_edge(1, 2, 2.0)
    gM.set_edge(1, 4, 1.0)

    gM.set_edge(3, 4, 3.0)

    gM.set_edge(4, 2, 3.0)
    gM.set_edge(4, 3, 3.0)

    print(gM.connections)

else:
    print("skipped")