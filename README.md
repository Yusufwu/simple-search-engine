# Simple Search Engine
Local search engine implemented in Python and deployed with Flask on Heroku:<br>
https://simple-search-engine.herokuapp.com/

The idea behind this project is to simulate a basic search engine. The search engine reads a file that contains lines of content (https://github.com/curlyfriesonionrings/simple-search-engine/blob/master/static/data/short_diagnoses.txt) and creates an inverted index. Each line of content is seen as a "document" in traditional search engine terms.

The actual search when given a query is performed using a [bitap algorithm](https://github.com/polovik/Algorithms/blob/master/bitap.py) with exact matching.
