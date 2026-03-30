import json
from collections import Counter
# use the 20-newsgroups dataset (pip install scikit-learn)
from sklearn.datasets import fetch_20newsgroups

from co_hits import calculate_cohits
from parsedocs import file_detail, file_parse_engine
from visualize_graph import graph_as_png
from one_mode import one_mode_projection
from graph_generator import generate_graph_as_png
from graph import graph_to_dict
from os import path
from pathlib import Path
startup_dir = Path(__file__).parent

#lambda
custom_lambda = 0.2
apply_additional_cleanup: bool = False

#load the dataset
#categories = ['sci.space', 'comp.graphics', 'rec.motorcycles']
#eval_index = 1
categories = ['comp.sys.ibm.pc.hardware', 'sci.electronics', 'misc.forsale', 'sci.med']
eval_index = 2

#query = ["nasa", "space", "engine"]
#query_index = 1
#query = ["data", "space", "system"]
#query_index = 2
#query = ["materials", "sales", "engine"]
#query_index = 3

query = ["financial", "electronic", "radiation", "matter"]
query_index = 1
#query = ["financial", "electronic", "radiation", "matter", "circuitry"]
#query_index = 2
#query = ["financial", "electronic", "radiation", "matter", "circuitry", "dominance"]
#query_index = 3

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
    
    # Process using the engine's logic
    if fd.text.strip():  # Skip empty documents
        fd.tokenize_text()
        file_list.append(fd)
    
    if i > 5000:
        break

if apply_additional_cleanup:
    #-- final clean up
    word_occurrence_limit = 0.2 ## upper limit of word frequency
    global_word_freq = Counter()
    for cur_file in file_list:
        file_words = set(cur_file.token_info.keys())
        global_word_freq.update(file_words)

    total_files = len(file_list)
    min_count = 25 # a word must be in at least 2 files
    max_count = total_files * 0.1  # ignore words in > 30% of files
    #generate secondary stop words
    secondary_stop_words = {
        word for word, count in global_word_freq.items() 
        if count < min_count or count > max_count
    }
        
    print(f"secondary_stop_words count: {len(secondary_stop_words)}")
    #-- clean up secondary stop words from files
    for cur_file in file_list:
        cur_file.remove_additional_stop_words(new_stop_words=secondary_stop_words)

print(f"Processing; {len(file_list)} files")

# generate a graph image
# graph_as_png(doc_keyword_map=file_list)

# Get the Co-HITS
print('getting co-hits')
doc_results, key_expansions, query_metrics = calculate_cohits(doc_keyword_map=file_list, q_keywords=query, lambda_scale=custom_lambda)
print(f'Got co-hits: {len(doc_results)}')

file_suffix =  f"{eval_index}_{query_index}_{("AggressiveClean" if apply_additional_cleanup else "NoCleanup")}"#{''.join(categories).replace(".","")}_{query_index}"#{''.join(query)}".replace(".","_")

#output JSON of the files
jData: str = json.dumps(file_list, default=lambda x: x.encode_for_json(), indent=4)
with open(path.join(startup_dir, f"test_json_{file_suffix}.json"), "w") as fw:
    fw.write(jData)
#output json of the query metrics
jData: str = json.dumps(query_metrics, default=lambda x: x.encode_for_json(), indent=4)
with open(path.join(startup_dir, f"qryStat_{file_suffix}.json"), "w") as fw:
    fw.write(jData)

#map file-id to filename
id_to_name = {doc.file_id: doc.file_name for doc in file_list}
readable_results = {id_to_name[fid]: score for fid, score in doc_results.items()}

sorted_doc_results = sorted(readable_results.items(), key=lambda item:item[1], reverse=True)
sorted_keyword_results = sorted(key_expansions.items(), key=lambda item:item[1], reverse=True)

top_10_docs = sorted_doc_results[:10]
top_10_keywords = sorted_keyword_results[:10]

print("--- Top 10 documents ---")
for doc_name, score in top_10_docs:
    print(f"{score:.4f} & {doc_name}")

print("--- Top 10 keywords ---")
for key_word, score in top_10_keywords:
    print(f"{score:.4f} & {key_word}")

#-- perform one-mode projection of top-10
projection = one_mode_projection(doc_keyword_map = file_list, 
                    docs_of_interest=[f_name for f_name, score in top_10_docs],
                    keywords_of_interest=[kw for kw, score in top_10_keywords])
#output JSON
jData: str = json.dumps(projection, default=graph_to_dict, indent=4)
with open(path.join(startup_dir, f"omp_{file_suffix}.json"), "w") as fw:
    fw.write(jData)

print("Done w/ one-mode")
#-- generate a png
generate_graph_as_png(g=projection, graph_file_name=path.join(startup_dir, f"one_mode_projection_{file_suffix}"))

print('Finished')