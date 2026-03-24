import json

from co_hits import calculate_cohits
from parsedocs import file_detail, file_parse_engine

# use the 20-newsgroups dataset (pip install scikit-learn)
from sklearn.datasets import fetch_20newsgroups

from visualize_graph import graph_as_png

from one_mode import one_mode_projection

from graph_generator import generate_graph_as_png

#load the dataset
categories = ['sci.space', 'comp.graphics', 'rec.motorcycles']
#categories = ['comp.sys.ibm.pc.hardware', 'sci.electronics', 'misc.forsale', 'sci.med']
newsgroups = fetch_20newsgroups(subset='train', categories=categories, remove=('headers', 'footers', 'quotes'))

# parse the docs
file_list: list[file_detail] = []
fP_engine = file_parse_engine()

for i in range(len(newsgroups.data)):
    # Create a virtual file detail
    # We use newsgroups.filenames[i] for path and file_id generation
    fd = file_detail(file_path=newsgroups.filenames[i], f_engine=fP_engine)
    
    # Manually inject the text from the dataset
    fd.text = newsgroups.data[i]
    
    # Process using your engine's logic
    if fd.text.strip():  # Skip empty documents
        fd.tokenize_text()
        file_list.append(fd)
    
    if i > 5000:
        break

print(f"Processing; {len(file_list)} files")

#output JSON
jData: str = json.dumps(file_list, default=lambda x: x.encode_for_json(), indent=4)
with open( "test_json.json", "w") as fw:
    fw.write(jData)

# generate a graph image
graph_as_png(doc_keyword_map=file_list)

# Get the Co-HITS
#query = ["nasa", "space", "engine"]
# query = ["data", "space", "system"]
query = ["materials", "sales", "engine"]

#query = ["financial", "electronic", "radiation", "matter"]
#query = ["financial", "electronic", "radiation", "matter", "circuitry"]
#query = ["financial", "electronic", "radiation", "matter", "circuitry"]
print('getting co-hits')
doc_results, key_expansions = calculate_cohits(file_list, query)
print(f'Got co-hits: {len(doc_results)}')

#map file-id to filename
id_to_name = {doc.file_id: doc.file_name for doc in file_list}
readable_results = {id_to_name[fid]: score for fid, score in doc_results.items()}

sorted_doc_results = sorted(readable_results.items(), key=lambda item:item[1], reverse=True)
sorted_keyword_results = sorted(key_expansions.items(), key=lambda item:item[1], reverse=True)

top_10_docs = sorted_doc_results[:10]
top_10_keywords = sorted_keyword_results[:10]

print("--- Top 10 documents ---")
for doc_name, score in top_10_docs:
    print(f"{score:.4f}\t{doc_name}")

print("--- Top 10 keywords ---")
for key_word, score in top_10_keywords:
    print(f"{score:.4f}\t{key_word}")

#-- perform one-mode projection
projection = one_mode_projection(doc_keyword_map = file_list, 
                    docs_of_interest=[f_name for f_name, score in sorted_doc_results],
                    keywords_of_interest=[kw for kw, score in sorted_keyword_results])

#-- generate a png
generate_graph_as_png(g=projection, graph_file_name="one_mode_projection.pngp")