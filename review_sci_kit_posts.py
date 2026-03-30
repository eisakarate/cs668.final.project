from sklearn.datasets import fetch_20newsgroups

#load the dataset
categories = ['sci.space', 'comp.graphics', 'rec.motorcycles']
#eval_index = 1
#categories = ['comp.sys.ibm.pc.hardware', 'sci.electronics', 'misc.forsale', 'sci.med']
#val_index = 2

newsgroups = fetch_20newsgroups(subset='train', categories=categories, remove=('headers', 'footers', 'quotes'))

post_id = 60103
print(newsgroups.data[post_id])