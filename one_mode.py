import visualize_graph
from collections import defaultdict
from itertools import combinations

from graph import Graph, Node, Edge

# perform one-mode projection
def one_mode_projection(doc_keyword_map, docs_of_interest, keywords_of_interest):
    #convert to set for optimization
    keys_set = set(keywords_of_interest)

    # generate a subgraph based on docs/keywords of interest
    selected_entries = []
    for doc in doc_keyword_map:
        if doc.file_name in docs_of_interest:
            #-- get keywords
            keyword_tokens = {k:count for k, count in doc.token_info.items() if k in keys_set}
            if keyword_tokens:
                selected_entries.append(
                    {
                        "file_name": doc.file_name, 
                        "token_info": keyword_tokens
                    }
                )

    # generate a bipartite graph from the document map
    b_graph = visualize_graph.To_bipartite_graph(doc_keyword_map=selected_entries)

    # Group files by their shared keywords
    keyword_map = defaultdict(list) #create an empty list
    #-- loop through the graph add keywords
    for entry in b_graph:
        #-- append the keyword and the associated file-name/weight (edge/node) information
        keyword_map[entry["keyword"]].append((entry["file_name"], entry["weight"]))

    # Project the edge into file-names
    # To create an edge between any two files sharing a keyword
    projections = defaultdict(float)
    #   loop through the keywords
    for keyword, files in keyword_map.items():
        # Get every unique pair of files that share this keyword
        #   Generate a unique set of every available pairs of (files) along with its weights
        for (file_a, weight_a), (file_b, weight_b) in combinations(files, 2):
            # Create a sorted tuple so (file1, file2) is the same as (file2, file1)
            edge = tuple(sorted((file_a, file_b))) + (keyword,)
            
            # perform the projection
            projections[edge] += (weight_a * weight_b)
    
    #-- convert to the GRAPH class we know and love
    #-- there may be a node w/o a edge to any of the keywords.. odd
    all_fileNames = set()
    for (f_a, f_b, kw) in projections.keys():
        all_fileNames.add(f_a)
        all_fileNames.add(f_b)
    for entry in b_graph:
        all_fileNames.add(entry["file_name"])

    file_names = list(all_fileNames)
    #-- undirected graph
    doc_graph = Graph(num_nodes=len(file_names), undirected=True)
    for (from_file, to_file, keyword), weight in projections.items():
        #get file index
        from_file_node_index = file_names.index(from_file)
        to_file_node_index = file_names.index(to_file)

        doc_graph.insert_edge(from_node=from_file_node_index, to_node=to_file_node_index, weight=weight, edge_label=keyword)

    #-- label the edges
    for cur_f in file_names:
        f_index = file_names.index(cur_f)
        doc_graph.nodes[f_index].label = cur_f

    return doc_graph