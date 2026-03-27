# pip install networkx
import networkx as nx
import matplotlib.pyplot as plt

from graph import Edge
from graph import Node
from graph import Graph
import graph

import random
import os

def has_edge(to_node_index: int, num_nodes: int, randomness_tuner: int = 1) -> bool:
    rand: int = (random.randint(0, num_nodes*randomness_tuner) % num_nodes)
    # if the random number match the node_index, then it has an edge
    return to_node_index == rand

def generate_random_graph(num_NodesToGenerate: int, randomnessTuner: int = 7, isUndirected: bool = True, allowSelfLoop: bool = False, defaultWeight:int = 1, useRandomWeight=False) -> Graph:

    # generate a graph of with 10 nodes
    randomGraph = Graph(num_nodes=num_NodesToGenerate, undirected=isUndirected)
    # for each node, randomly assign edges to its neighbors
    for curN in range(num_NodesToGenerate):
        for possibleNode in range(num_NodesToGenerate):
            if(curN != possibleNode) or (allowSelfLoop):
                if has_edge(to_node_index=possibleNode, num_nodes=num_NodesToGenerate, randomness_tuner=randomnessTuner):
                    cur_weight = defaultWeight
                    if useRandomWeight:
                        cur_weight = (random.randint(0, num_NodesToGenerate*randomnessTuner) % num_NodesToGenerate)
                    randomGraph.insert_edge(from_node=curN, to_node=possibleNode, weight=defaultWeight)
                    print(f'added edge: [{curN}] - [{possibleNode}] ')
    
    return randomGraph

def generate_graph_as_png(g: Graph, graph_file_name: str = "graph"):
    # # output local clustering coefficient
    # for n in range(g.num_nodes):
    #     cf = graph.clustering_coefficient(g=g, ind=n)
    #     print(f'Clustering Coefficient for {n} is [{cf}]')
    # # output average clustering coefficient
    # avgCF = graph.average_clustering_coefficient(g=g)
    # print(f'Average Clustering Coefficient: {avgCF}')

    # generate a copy of the graph in networkx
    nxG = nx.Graph()
    if not g.undirected:
        nxG = nx.DiGraph()      # setup a digraph

    # register the nodes
    for n in range(g.num_nodes):
        nxG.add_node(n)
    # register edges
    for curNode in g.nodes:
        for e in curNode.get_edge_list():
            nxG.add_edge(e.from_node, e.to_node, weight=e.weight,
                         label_text=f"{e.label}({e.weight})")

    # draw node labels
    node_labels = {n.index: (n.label if n.label else n.index) for n in g.nodes}

    #Setup Layout (Important for consistent edge label placement)
    pos = nx.spring_layout(nxG) 

    #draw the nodes and labels 
    nx.draw_networkx_nodes(nxG, pos, node_color='lightblue')
    nx.draw_networkx_labels(nxG, pos, labels=node_labels)

    # draw it
    if g.undirected:
        nx.draw_networkx_edges(nxG, pos)
    else:
        nx.draw(nxG, pos, 
                # labels=node_labels,
                # with_labels=True, 
                # node_color='lightblue', 
                # node_size=500,
                # font_size=10,
                arrowstyle='-|>', 
                arrowsize=20,
                connectionstyle='arc3,rad=0.2')
    
    # Draw the edge weights specifically
     # Use label_pos=0.3 to slide the text along the curve 
    #  so they don't stack on top of each other in the center
    edge_labels = {edge: v for edge, v in nx.get_edge_attributes(nxG, 'label_text').items()}
    nx.draw_networkx_edge_labels(nxG, pos, 
                                 edge_labels=edge_labels,
                                 label_pos=0.3, 
                                 font_size=9)

    #output
    import matplotlib.pyplot as plt
    script_dir = os.path.dirname(os.path.abspath(__file__))

    plt.savefig(os.path.join(script_dir,f"{graph_file_name}.png"), format="PNG", dpi=300, bbox_inches = 'tight')
    plt.show()