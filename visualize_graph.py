from parsedocs import file_detail, file_parse_engine

import networkx as nx
import plotly as plt
import plotly.graph_objects as go

def To_bipartite_graph(doc_keyword_map):
    output = []
    #-- generate a map
    for detail in doc_keyword_map:
        for keyword, occurrence in detail.word_token_summary.items():
            output.append({
                "file_name": detail.file_name,
                "keyword": keyword,
                "weight": occurrence
            })

    return output

def graph_as_png(doc_keyword_map):
    
    weighted_graph_inf = To_bipartite_graph(doc_keyword_map=doc_keyword_map)

    graph = nx.Graph()

    # setup nodes list
    files = list(set(d['file_name'] for d in weighted_graph_inf))
    keywords = list(set(d['keyword'] for d in weighted_graph_inf))

    graph.add_nodes_from(files, bipartite=0)   # Set 0
    graph.add_nodes_from(keywords, bipartite=1) # Set 1

    # add edges
    for cur_doc_keyword in weighted_graph_inf:
        graph.add_edge(
            cur_doc_keyword['file_name'],
            cur_doc_keyword['keyword'],
            weight = cur_doc_keyword['weight']
        )
    
    # setup Bipartite Layout Positions
    pos = nx.bipartite_layout(graph, files)

    # create edge lines
    edge_x, edge_y = [], []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#888'), 
                            #hoverinfo='none', 
                            mode='lines')

    # draw nodes
    node_x, node_y, node_text, node_color = [], [], [], []
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"<b>{node}</b>")
        node_color.append('skyblue' if node in files else 'lightgreen')
    
    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        text=[n if n in files else "" for n in graph.nodes()], # Only label file nodes initially
        #textposition="top center", hoverinfo='text', 
        hovertext=node_text,
        marker=dict(color=node_color, size=20, line_width=2)
    )
    
    #draw the graph
    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='Interactive Bipartite File-Keyword Graph',
                #showlegend=False,
                #xaxis=dict(
                    #showgrid=False, zeroline=False, showticklabels=False
                #    ),
                #yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
             ))
    
    #save it as html (FUN)
    fig.write_html("bipartite_graph_output.html")