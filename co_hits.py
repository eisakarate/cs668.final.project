import json
# used to capture metrics
class co_hits_metrics:
    def __init__(self, query, iteration:int, num_docs:int, num_keywords:int):
        self.query = query
        self.iteration = iteration
        self.num_docs = num_docs
        self.num_keywords = num_keywords
    
    def encode_for_json(self):
        return {
            "initial_query": ",".join(self.query),
            "iteration": self.iteration,
            "num_docs": self.num_docs,
            "num_keywords": self.num_keywords,
        }

class matrix_info:
    def __init__(self, w, num_docs: int, num_keywords:int, file_id_list, file_id_index_map, keyword_list, keyword_index_map ):
        self.w_matrix = w
        self.num_docs = num_docs
        self.num_keywords = num_keywords
        self.file_id_list = file_id_list
        self.file_id_index_map = file_id_index_map
        self.keyword_list = keyword_list
        self.keyword_index_map = keyword_index_map

#--- converts the weighted bipartite graph (in JSON format) into an adjacency matrix
#--     JSON Schema:
#--         [
#--             {
#--                 "file_name": "t",
#--                 "file_path": "",
#--                 "file_ext": "",
#--                 "file_id": "",
#--                 "token_info": {
#--                     "": 1,
#--                     "": 1,
#--                     "": 1,
#--                     "": 1
#--                 }
#--             },
#--             ...
#--         ]
def convert_json_to_adjacency_matrix(doc_keyword_map) -> matrix_info:
    # get file ids
    file_ids = [cur_doc.file_id for cur_doc in doc_keyword_map]
    # get unique list of all the keywords
    keywords_list: set = set()
    for cur_doc in doc_keyword_map:
        keywords_list.update(cur_doc.token_info.keys())

    #-- sort the keywords
    keywords_list_sorted = sorted(list(keywords_list))

    # generate the matrix (W) of U x V
    num_docs:int = len(file_ids)
    num_keywords: int = len(keywords_list_sorted)
    #-- map the keyword to index 
    document_to_idx_map = {doc: i for i, doc in enumerate(file_ids)}
    keyword_to_idx_map = {word: i for i, word in enumerate(keywords_list_sorted)}

    #-- build the matrix    
    W = [[0.0] * num_keywords for _ in range(num_docs)]
    for doc_index, item in enumerate(doc_keyword_map):
        for cur_keyword, cur_word_occurrence in item.token_info.items():
            #get the keyword index (this is similar to how we calculated node/index)
            j = keyword_to_idx_map[cur_keyword]
            # set the matrix's value, i.e., weight
            W[doc_index][j] = float(cur_word_occurrence)

    return matrix_info(w=W, num_docs= num_docs, num_keywords= num_keywords, file_id_list=file_ids, file_id_index_map=document_to_idx_map, keyword_list= keywords_list_sorted, keyword_index_map= keyword_to_idx_map)

def calculate_cohits(doc_keyword_map, q_keywords, lambda_scale = 0.8, cnt_iteration: int = 10):
    #-- generate the initial adjacency matrix (x_0, y_0)
    init_matrix_info = convert_json_to_adjacency_matrix(doc_keyword_map=doc_keyword_map)

    #-- generate transition matrix, note: we normalize the scores (like HITS)
    #-- normalization: cur_score_i_j / total_score_i
    #--     total_score_i = sum(scores_i_j)
    # W_u (document -> keyword) with normalized score
    W_u = []
    for i in range(init_matrix_info.num_docs):
        doc_total = sum(init_matrix_info.w_matrix[i])
        W_u.append([init_matrix_info.w_matrix[i][j] / doc_total if doc_total > 0 else 0 for j in range(init_matrix_info.num_keywords)])

    # Wv (keyword -> document) with normalized score
    W_v = [[0.0] * init_matrix_info.num_docs for _ in range(init_matrix_info.num_keywords)]
    for j in range(init_matrix_info.num_keywords):
        keyword_total = sum(init_matrix_info.w_matrix[i][j] for i in range(init_matrix_info.num_docs))
        W_v[j] = [init_matrix_info.w_matrix[i][j] / keyword_total if keyword_total > 0 else 0 for i in range(init_matrix_info.num_docs)]

    # Setup x,y lists
    #-- This represents (W_0)
    #-- initialize document score (x_i) to 0
    x_init = [0.0] * init_matrix_info.num_docs
    #-- initialize keyword scores (y_i) to 0, except for those words that are part of the query expression.  
    #--     seed those as "have score" of (1)
    y_init = [1.0 if cur_word.lower() in [q.lower() for q in q_keywords] else 0.0 for cur_word in init_matrix_info.keyword_list]
    
    # set current scores (pre-iteration)
    u_scores = list(x_init)
    v_scores = list(y_init)

    # metrics
    query_metrics = []
    query_metrics.append(co_hits_metrics(iteration=0, query=q_keywords, num_docs=0, num_keywords=sum(1 for x in y_init if x > 0)) )

    # Initialize keywords trackers that have already been "seen"
    seen_keyword_indices = {j for j, score in enumerate(v_scores) if score > 0}
    keywordsByIteration = {}

    # iterate
    for iteration_index in range(cnt_iteration):
        # update document (x_i) scores: x = (1 - lam) * x_init + lam * (Wv * v), equation (3)
        updated_u_scores = []
        for i in range(init_matrix_info.num_docs):
            # sum the document scores (based on total occurrence of keywords in the query)
            keyword_sum = sum(W_v[j][i] * v_scores[j] for j in range(init_matrix_info.num_keywords))
            updated_u_scores.append((1 - lambda_scale) * x_init[i] + lambda_scale * keyword_sum)
        
        # Update keyword scores (y_i): y = (1 - lam) * y_init + lam * (Wu^T * u), equation (4)
        updated_v_scores = []
        for j in range(init_matrix_info.num_keywords):
            # Summation represents the Matrix Multiplication (Wu^T * u)
            document_sum = sum(W_u[i][j] * updated_u_scores[i] for i in range(init_matrix_info.num_docs))
            updated_v_scores.append((1 - lambda_scale) * y_init[j] + lambda_scale * document_sum)

        # check the difference
        # get the keywords "active" in this iteration (score > 0)
        current_active_keyword_indices = {j for j, score in enumerate(updated_v_scores) if score > 0}
        
        # identify the new keyword indices
        new_keyword_indices = current_active_keyword_indices - seen_keyword_indices
        
        # Map new new keywords indices to words 
        new_keywords = [init_matrix_info.keyword_list[idx] for idx in new_keyword_indices]
        #print(f'Iteration {iteration_index + 1} - new_keywords: {new_keywords}')
        keywordsByIteration[iteration_index] = new_keywords
        # add to the tracker
        seen_keyword_indices.update(new_keyword_indices)

        #-- store the the new scores
        u_scores = updated_u_scores
        v_scores = updated_v_scores

        #-- update the metrics
        query_metrics.append(
            co_hits_metrics(
                iteration=iteration_index, 
                query=q_keywords,
                num_docs=sum(1 for x in u_scores if x > 0), 
                num_keywords=sum(1 for x in v_scores if x > 0)
            )
        )
    
    print(f"Unique IDs: {len(set(init_matrix_info.file_id_list))}")
    print(f'u_scores has: {len(u_scores)} entries')

    #-- output as JSON
    jData: str = json.dumps(keywordsByIteration, indent=4)
    file_suffix = f"{'_'.join(q_keywords)}".replace(".","_")
    with open(f"new_keywords_{file_suffix}.json", "w") as fw:
        fw.write(jData)
    
    #-- return, associate the score-index with original content
    return dict(zip(init_matrix_info.file_id_list, u_scores)), dict(zip(init_matrix_info.keyword_list, v_scores)), query_metrics