from flask import Flask, request
from markupsafe import escape
from flask import render_template
from elasticsearch import Elasticsearch
import math
import warnings
import urllib3


# Change pasword
ELASTIC_PASSWORD = "myELASTICSEARCH2003"

es = Elasticsearch("https://localhost:9200", http_auth=("elastic", ELASTIC_PASSWORD), verify_certs=False)
app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    page_size = 10

    keyword = request.args.get('keyword') #recieve the input form searcher
    if not keyword:
        return render_template('search.html', keyword=keyword, hits=[], page_no=page_no, page_total=0)

    if request.args.get('page'):
        page_no = int(request.args.get('page'))
    else:
        page_no = 1

# check when user type like 3 bedroom
    numeric_field = None
    numeric_value = None
    if 'bedroom' in keyword.lower():
        numeric_field = 'Bedrooms'
    elif 'bathroom' in keyword.lower():
        numeric_field = 'Bathrooms'

    # Determine if the keyword is numeric (for searching numeric fields)
    try:
        # convert keyword to float
        numeric_keyword = float(keyword)
        numeric_search = True
    except ValueError:
        # If it fails, treat the keyword as a string
        numeric_search = False

    # Construct the body of the search query
    body = {
        'size': page_size,
        'from': page_size * (page_no - 1),
        'query': {
            'bool': {
                'should': []
            }
        }
    }

    # Add fuzzy match for string fields if it's not numeric
    # if not numeric_search:
    #     body['query']['bool']['should'].append({
    #         'multi_match': {
    #             'query': keyword,
    #             'fields': ['Villa Name^3', 'Facilities^2', 'Address^2'],  # Only apply fuzzy match to text fields
    #             'operator': 'or',
    #             'type': 'best_fields',
    #             'fuzziness': 'AUTO',
    #             'prefix_length': 1
    #         }
    #     })
    try:
        # Extract the numeric value from the keyword
        numeric_value = int(''.join(filter(str.isdigit, keyword)))
    except ValueError:
        numeric_value = None

    # Add query based on numeric field or generic keyword
    if numeric_field and numeric_value is not None:
        body['query']['bool']['should'].append({
            'term': {
                numeric_field: numeric_value  # Match the numeric value in the appropriate field
            }
        })
    # search 
    if not numeric_search:
        body['query']['bool']['should'].extend([
            {
                'multi_match': {
                    'query': keyword,
                    'fields': ['Villa Name^3', 'Facilities^2', 'Address^2'],  # Only apply fuzzy match to text fields
                    'operator': 'or',
                    'type': 'best_fields',
                    'fuzziness': 'AUTO',
                    'prefix_length': 1
                }
            },
            {
                'wildcard': {
                    'Villa Name': f"*{keyword.lower()}*"
                }
            },
            {
                'wildcard': {
                    'Facilities': f"*{keyword.lower()}*"
                }
            },
            {
                'wildcard': {
                    'Address': f"*{keyword.lower()}*"
                }
            }
        ])
    else:
    # Query for numeric fields (e.g., Price, Distance to Beach, Bedrooms, Bathrooms)
        body['query']['bool']['should'].extend([
            {
                'wildcard': {
                    'Price': f"*{keyword.lower()}*"
                }
            },
            {
                'wildcard': {
                    'Distance to Beach (KM)': f"*{keyword.lower()}*"
                }
            },
            {
                'wildcard': {
                    'Bedrooms': f"*{keyword.lower()}*" # Exact match for Bathrooms
                }
            },
            {
                'wildcard': {
                    'Bathrooms': f"*{keyword.lower()}*"
                }
            }
    ])
        

    # Add exact match for numeric fields if the keyword is numeric
    # if numeric_search:
    #     body['query']['bool']['should'].expend({
    #         'multi_match': {
    #             'query': keyword,
    #             'fields': ['Price', 'Distance to Beach (KM)', 'Bedrooms', 'Bathrooms'],  # Numeric fields for exact match
    #             'operator': 'or',
    #             'type': 'best_fields'
    #         }
    #     }) //ver1
        
    try:
        res = es.search(index='pool_data', body=body)
        print("Elasticsearch response:", res)
        # hits = [{'Villa Name': doc['_source']['Villa Name'], 'facilities': doc['_source']['facilities'], 'created': doc['_source']['created']} for doc in res['hits']['hits']]
        hits = [
            {
                'Score': doc['_score'],
                'Villa Name': doc['_source']['Villa Name'],
                'Facilities': doc['_source']['Facilities'],
                'Bedrooms' : doc['_source']['Bedrooms'],
                'Bathrooms' : doc['_source']['Bathrooms'],
                'Address': doc['_source']['Address'],
                'Price': doc['_source']['Price'],
                'Distance to Beach (KM)': doc['_source']['Distance to Beach (KM)'],
                'Villa Link': doc['_source']['Villa Link'],
                'Villa Image': doc['_source']['Villa Image']
            }
            for doc in res['hits']['hits']
        ]
        
        page_total = math.ceil(res['hits']['total']['value']/page_size)
        return render_template('search.html',keyword=keyword, hits=hits, page_no=page_no, page_total=page_total)

    except Exception as e:
        print(f"Error during search: {e}")
        return render_template('search.html', keyword=keyword, hits=[], page_no=page_no, page_total=0, error_message="An error occurred during the search.")
    
    if __name__ == "__main__":
        app.run(debug=True)
    
    print("Search Results:", res)


