from flask import Flask, render_template, request
from operator import itemgetter
from collections import defaultdict
from array import array
import re

app = Flask(__name__)

class SearchEngine:
    
    def __init__(self):
        ''' Reverse index dictionary '''
        self.index = defaultdict(list)
        ''' Document ID: term dictionary '''
        self.docLookup = {}

    ''' Given a stream of text, return the cleaned terms from the text '''
    def getTerms(self, line):
        line = line.lower()
        line = re.sub(r'[^a-z0-9\' ]', ' ', line)
        line = line.split()
        return line

    ''' Reads each line from a text file and creates a reverse index dictionary '''
    def createIndex(self):
        # Each line in input is treated as a document
        docID = 0
        
        # Create both the reverse index and regular look up table
        with open('./static/data/short_diagnoses.txt', 'r') as colFile:
            for line in colFile:
                self.docLookup[docID] = line
                terms = self.getTerms(line)
                for term in terms:
                    self.index[term].append(docID)

                docID += 1

    ''' Returns a list of document IDs that the query was found in '''
    def oneWordQuery(self, q):
        originalQuery = q
        q = self.getTerms(q)
        if len(q) == 0:
            return []
        elif len(q) > 1:
            return self.freeTextQuery(originalQuery)
        
        # q contains only 1 term - proceed with bitap search
        q = q[0]
        result = []
        for term in self.index.keys():
            (needlePlace, errors) = self.bitapSearch(term, q, 0)
            if not needlePlace == '':
                result += self.index[term]

        result.sort()
        
        return result

    ''' Returns a list of document IDs that the query was found in '''
    def freeTextQuery(self, q):
        q = self.getTerms(q)
        if len(q) == 0:
            return []

        # Run one word query for all terms in query
        result = []
        for term in q:
            result += self.oneWordQuery(term)

        result = list(set(result))
        result.sort()
        
        return result

    ''' Converts a list of document IDs into a list of string results '''
    def idToText(self, idList):
        return [self.docLookup[x] for x in idList]

    """
    Extracted from: https://github.com/polovik/Algorithms/blob/master/bitap.py

    Modified to work within context
    """
    def bitapSearch(self, haystack, needle, maxErrors):
        haystackLen = len(haystack)
        needleLen = len(needle)

        """Genarating mask for each letter in haystack.
        This mask shows presence letter in needle.
        """
        def _generateAlphabet(needle, haystack):
            alphabet = {}
            for letter in haystack:
                if letter not in alphabet:
                    letterPositionInNeedle = 0
                    for symbol in needle:
                        letterPositionInNeedle = letterPositionInNeedle << 1
                        letterPositionInNeedle |= int(letter != symbol)
                    alphabet[letter] = letterPositionInNeedle
            return alphabet

        alphabet = _generateAlphabet(needle, haystack)

        table = [] # first index - over k (errors count, numeration starts from 1), second - over columns (letters of haystack)
        emptyColumn = (2 << (needleLen - 1)) - 1

        #   Generate underground level of table
        underground = []
        [underground.append(emptyColumn) for i in range(haystackLen + 1)]
        table.append(underground)

        #   Execute precise matching
        k = 1
        table.append([emptyColumn])
        for columnNum in range(1, haystackLen + 1):
            prevColumn = (table[k][columnNum - 1]) >> 1
            letterPattern = alphabet[haystack[columnNum - 1]]
            curColumn = prevColumn | letterPattern
            table[k].append(curColumn)
            if (curColumn & 0x1) == 0:
                place = haystack[columnNum - needleLen : columnNum]
                return (place, k - 1)

        #   Execute fuzzy searching with calculation Levenshtein distance
        for k in range(2, maxErrors + 2):
            table.append([emptyColumn])

            for columnNum in range(1, haystackLen + 1):
                prevColumn = (table[k][columnNum - 1]) >> 1
                letterPattern = alphabet[haystack[columnNum - 1]]
                curColumn = prevColumn | letterPattern
                
                insertColumn = curColumn & (table[k - 1][columnNum - 1])
                deleteColumn = curColumn & (table[k - 1][columnNum] >> 1)
                replaceColumn = curColumn & (table[k - 1][columnNum - 1] >> 1)
                resColumn = insertColumn & deleteColumn & replaceColumn
                
                table[k].append(resColumn)
                if (resColumn & 0x1) == 0:
                    startPos = max(0, columnNum - needleLen - 1) # taking in account Replace operation
                    endPos = min(columnNum + 1, haystackLen) # taking in account Replace operation
                    place = haystack[startPos : endPos]
                    return (place, k - 1)
                
        return ("", -1)


@app.route("/")
def homepage():
    html = render_template('index.html')
    return html

@app.route("/results")
def results():
    searchEngine = SearchEngine()
    searchEngine.createIndex()
    
    # Determine query type (one word or free text)
    q =  request.args.get('query')
    resIds = []
    if len(q.split()) > 1:
        resIds = searchEngine.freeTextQuery(q)
    else:
        resIds = searchEngine.oneWordQuery(q)
    
    res = searchEngine.idToText(resIds)

    html = render_template('results.html', query=q, results=res)
    return html

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
