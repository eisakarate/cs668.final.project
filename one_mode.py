import visualize_graph
from collections import defaultdict
from itertools import combinations
from parsedocs import file_detail, file_parse_engine
from co_hits import calculate_cohits

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

        #check if an edge exists
        if doc_graph.is_edge(from_node=from_file_node_index, to_node=to_file_node_index):
            #-- existing, add to the total weight
            cur_node = doc_graph.get_edge(from_node=from_file_node_index, to_node=to_file_node_index)
            cur_node.weight = cur_node.weight + weight
            cur_node = doc_graph.get_edge(from_node=to_file_node_index, to_node=from_file_node_index)
            cur_node.weight = cur_node.weight + weight
        else:
            #-- new add the edge
            doc_graph.insert_edge(from_node=from_file_node_index, to_node=to_file_node_index, weight=weight, edge_label=keyword)

    #-- label the edges
    for cur_f in file_names:
        f_index = file_names.index(cur_f)
        doc_graph.nodes[f_index].label = cur_f

    return doc_graph

if __name__ == "__main__":
    
    fP_engine = file_parse_engine()
    #mockup a path
    d = [
        file_detail(file_path="test_files/doc1.txt", f_engine=fP_engine),
        file_detail(file_path="test_files/doc2.txt", f_engine=fP_engine),
        file_detail(file_path="test_files/doc3.txt", f_engine=fP_engine)
    ]

    for cur_d in d:
        cur_d.load_text()
        cur_d.tokenize_text()

    doc_results, key_expansions, query_metrics = calculate_cohits(doc_keyword_map=d, q_keywords=["v_1", "v_2"], lambda_scale=0.8)
    
    #all the docs and keywords
    docs_of_interest = ["doc1.txt", "doc2.txt", "doc3.txt"]  # List of file names
    keywords_of_interest = ["test", "eye"]  # List of keywords to consider

    #calculate
    doc_graph = one_mode_projection(doc_keyword_map = d, docs_of_interest = docs_of_interest, keywords_of_interest = keywords_of_interest)
    print(doc_graph.num_nodes)
    #-- print
    for cur_n in doc_graph.nodes: 
        for cur_e in cur_n.get_edge_list():
            print(f"({doc_graph.nodes[cur_e.from_node].label}, {doc_graph.nodes[cur_e.to_node].label}) - Weight: {cur_e.weight}")