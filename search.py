from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StemmingAnalyzer, LowercaseFilter
from whoosh.scoring import BM25F
from pymongo import MongoClient
import os
import spacy

nlp = spacy.load("en_core_web_sm")
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

MONGO_URI = "mongodb+srv://nghednh:123@cluster0.llhn1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

movie_analyzer = StemmingAnalyzer() | LowercaseFilter()

schema = Schema(
    movie_id=ID(stored=True, unique=True),
    name=TEXT(stored=True, analyzer=movie_analyzer, field_boost=2.0),  # Boosted importance
    overview=TEXT(stored=True, analyzer=movie_analyzer),
    subtitle=TEXT(stored=True, analyzer=movie_analyzer)
)
client = MongoClient(MONGO_URI)
db = client['movie_db']
collection = db['movies']

INDEX_DIR = "movie_text_index"
def _get_index(index_dir=INDEX_DIR):
    try:
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        if not os.listdir(index_dir):  # Check if the directory is empty
            return create_in(index_dir, schema)
        return open_dir(index_dir)
    except Exception as e:
        print(f"Error initializing index: {e}")
        raise

def expand_query(query):
    doc = nlp(str(query))
    expanded_terms = []

    expanded_terms.append(query)

    for token in doc:
        if not token.is_stop and not token.is_punct:
            expanded_terms.append(token.text)
            if token.lemma_ != token.text:
                expanded_terms.append(token.lemma_)
    for ent in doc.ents:
        expanded_terms.append(ent.text)

    return " OR ".join(set(expanded_terms))

def update_index(batch_size=2000):
    index = _get_index()
    print("Starting index update...")
    writer = index.writer()

    try:
        total_docs = collection.count_documents({})
        processed = 0

        with index.searcher() as searcher:
            for movie in collection.find().batch_size(batch_size):
                existing = searcher.document(movie_id=str(movie['movie_id']))
                if existing:
                    print(f"Skipping duplicate movie_id: {movie['movie_id']}")
                    continue
                writer.update_document(
                    movie_id=str(movie['movie_id']),
                    name=movie['name'],
                    overview=movie['overview'],
                    subtitle=movie.get('subtitle', '')
                )

                processed += 1
                if processed % batch_size == 0:
                    print(f"Processed {processed}/{total_docs} documents")

        writer.commit()
        print(f"Index update complete. Total processed: {processed}/{total_docs}")

    except Exception as e:
        writer.cancel()
        print(f"Error updating index: {e}")
        raise

def search_movies(query):
    try:
        index = _get_index()
        query_str = str(query)
        expanded_query = expand_query(query_str)
        seen_movie_ids = set()
        results_with_scores = []
        with index.searcher(weighting=BM25F) as searcher:
            query_parsed = MultifieldParser(["overview", "name"], index.schema).parse(expanded_query)
            results = searcher.search(query_parsed)
            if results:
                for r in results:
                    movie_id = r.get('movie_id')
                    movie_name = r.get('name')
                    if movie_id not in seen_movie_ids and movie_name not in seen_movie_ids:
                        seen_movie_ids.add(movie_id)
                        seen_movie_ids.add(movie_name)
                        results_with_scores.append((movie_id, movie_name, r.score))
            else:
                print("No results found for the query.")

            return results_with_scores

    except Exception as e:
        print(f"Search error: {e}")
        return []
def getID_search_movies(query):
    try:
        index = _get_index()
        query_str = str(query)
        expanded_query = expand_query(query_str)
        seen_movie_ids = set()
        movie_ids = []
        with index.searcher(weighting=BM25F) as searcher:
            query_parsed = MultifieldParser(["overview", "name"], index.schema).parse(expanded_query)
            results = searcher.search(query_parsed)
            if results:
                for r in results:
                    movie_id = r.get('movie_id')
                    if movie_id not in seen_movie_ids:
                        seen_movie_ids.add(movie_id)
                        movie_ids.append(movie_id)
            else:
                print("No results found for the query.")
            return movie_ids
    except Exception as e:
        print(f"Search error: {e}")
        return []
if __name__ == "__main__":
    update_index()
    query = "Venom and Eddie"
    results = search_movies(query)
    if results:
        for movie_id, movie_name, score in results:
            print(f"Movie: {movie_name}")
            print(f"Score: {score:.2f}")
            print("-" * 50)
