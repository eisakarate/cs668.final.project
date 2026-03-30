import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt') # 'punkt' is needed for word tokenization
nltk.download('punkt_tab') # 'punkt' is needed for word tokenization

from collections import Counter

from pathlib import Path

import json

import uuid
import hashlib
import string

#-- pip install python-docx
from docx import Document
 
class file_parse_engine: 
    def __init__ (self):
        # download default stop-words corpus
        try:
            nltk.data.find('corpora/stopwords')
        except nltk.downloader.DownloadError:
            nltk.download('stopwords')
        try:
            nltk.data.find('tokenizers/punkt')
        except nltk.downloader.DownloadError:
            nltk.download('punkt')

        #additional stop words
        addtional_stopwords = {'would', 'one', 'also', 'like','get', 'do', 'not', 'no' }

        # define stop words (english)
        self.stop_words = set(stopwords.words('english')) | addtional_stopwords
        self.punctuations = set(string.punctuation)
        #add lemmatization
        self.lemmatizer = nltk.stem.WordNetLemmatizer()

    # remove stop-words
    def remove_stopwords(self, text:str):
        # Tokenize the text
        word_tokens:list = word_tokenize(text.lower())

        # Filter out stop words using a list comprehension
        filtered_words = [self.lemmatizer.lemmatize(word) for word in word_tokens 
                          if word.lower() not in self.stop_words
                          and word not in self.punctuations
                          and word.isalpha()
                          and len(word) > 2]

        return filtered_words

    def generate_graph_source(self, text:str):
        # clean up 
        discovered_tokens:list = self.remove_stopwords(text)

        # get word + counts
        word_counts = Counter(discovered_tokens)

        return word_counts

    # read ms_word (.doc or .docx)
    def get_text_from_ms_word(self, file_path: str) -> str:
        doc: Document = Document(file_path)
        full_text: list = []
        for cur_paragraph in doc.paragraphs:
            full_text.append(cur_paragraph.text)
        
        return "\n".join(full_text)

    #read markdown files
    def get_text_from_markdown(self, file_path:str) -> str:
        # markdown files are just text-files anyway
        return self.get_text_from_textfile(file_path=file_path)

    # read text files
    def get_text_from_textfile(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Specified file was not found. {file_path}")
            return None
        except Exception as e:
            print(f"Error reading file ({file_path}): {e}")
            return None
    
    def get_hash_from_file(self, file_path: str, hash_algorithm: str = 'sha512') -> str:
        #-- setup the hash function
        h_func = hashlib.new(hash_algorithm)

        with open(file_path, mode='rb') as f_hash:  #open in read-only, binary
            #-- read by chucks
            while cur_chunk := f_hash.read(65536):
                h_func.update(cur_chunk)

        #-- output the hash
        return h_func.hexdigest()
    
    def get_hash_from_text(self, source_text: str, hash_algorithm: str = 'sha512') -> str:
        #-- setup the hash function
        h_func = hashlib.new(hash_algorithm)
        #-- hash the text
        h_func.update(source_text.encode('utf-8'))

        hash_str = h_func.hexdigest()
        #-- print(hash_str)
        #-- output the hash
        return hash_str

class file_detail:
    def __init__(self, file_path:str, f_engine: file_parse_engine, f_alt_id: str=""):
        self.file_path = file_path
        self.file_id = ""
        self.text = ""
        self.word_token_summary = None
        self.token_info = None
        self.file_parse_engine = f_engine
        self.alternate_file_id = f_alt_id

    @property
    def file_name(self):
        return Path(self.file_path).name
    
    @property
    def file_extension(self):
        return Path(self.file_name).suffix

    # load text from source
    def load_text(self):
        match self.file_extension:
            case ".doc"| ".docx":
                self.text = self.file_parse_engine.get_text_from_ms_word(file_path=self.file_path)
            case ".md":
                self.text = self.file_parse_engine.get_text_from_markdown(file_path=self.file_path)
            case ".txt":
                self.text = self.file_parse_engine.get_text_from_textfile(file_path=self.file_path)
            case _:
                print(f"file extension ({self.file_extension}) is not supported.")
                raise NotImplementedError(f"file extension ({self.file_extension}) is not supported.")

    # parse text
    def tokenize_text(self):
        self.word_token_summary = self.file_parse_engine.generate_graph_source(text=self.text)
        self.token_info = dict(self.word_token_summary)
        #load the hash
        self.file_id = self.file_parse_engine.get_hash_from_text(source_text=self.text)

    # remove additional stop words
    def remove_additional_stop_words(self, new_stop_words: set):
        # remove additional stopwords
        print(f"Before Prune: {len(self.token_info)}")
        if self.token_info:
            self.token_info = {
                word: count for word, count in self.token_info.items() 
                if word not in new_stop_words
            }
        print(f"After Prune: {len(self.token_info)}")

    def encode_for_json(self):
        return {
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_ext": self.file_extension,
            "file_id":  self.file_id,  ## hash
            "token_info": self.token_info, # convert to dictionary,
            #"file_id_alt": self.f_alt_id,
            "file_text": self.text
        }

if __name__ == "__main__":
    #start up
    fP_engine = file_parse_engine()

    path_to_evaluate: str = r"F:\Git\EHA\documents\EHA.1.0\RequirementsSpecifications"
    dir_path = Path(path_to_evaluate)

    #read all the files
    files_found:list = [x for x in dir_path.rglob("*") if x.is_file()] # *.md ?? *.txt ?? *.docx

    fd_listing: list[file_detail] = []

    skipped_files: list = []
    for cur_f in files_found:
        #print("Cur File: " + str(cur_f.resolve()))
        try:
            fd: file_detail = file_detail(
                file_path=str(cur_f.resolve()),
                f_engine=fP_engine)
            fd.load_text()
            fd.tokenize_text()

            #append the file
            fd_listing.append(fd)
        except Exception as e:
            #print(f"Skipped file - Error reading file ({str(cur_f.resolve())}): {e}")
            skipped_files.append(str(cur_f.resolve()))

    # fd: file_detail = file_detail(
    #     file_path=r"F:\Git\EHA\documents\EHA.1.0\RequirementsSpecifications\2025.05.GenderDysphoria\2025.05.GenderDysphoraImplementation.md",
    #     f_engine=fP_engine)
    # fd.load_text()

    # print(fd.text)
    # fd.tokenize_text()

    # #append the file
    # fd_listing.append(fd)

    #output as json
    jData: str = json.dumps(fd_listing, default=lambda x: x.encode_for_json(), indent=4)
    with open( "test_json.json", "w") as fw:
        fw.write(jData)

    print(f"Processed: {len(files_found)} files")
    if len(skipped_files) > 0:
        print(f"Files skipped: {len(skipped_files)} files")
        for cur_skipped_file in skipped_files:
            print(f"\t{cur_skipped_file}")