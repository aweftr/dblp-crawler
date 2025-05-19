# %%
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper(
    "https://sparql.dblp.org/sparql"
)
sparql.setReturnFormat(JSON)

# %%
query = """PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?title ?publishedin ?year WHERE {
  ?publ dblp:publishedIn ?publishedin .
  ?publ dblp:title ?title .
  ?publ dblp:yearOfPublication ?year .
  FILTER regex(?title, "over-subs", "i")
  FILTER REGEX(?publishedin, "icdcs", "i")
}
ORDER BY DESC(?year)
LIMIT 10
"""
sparql.setQuery(query)
try:
    ret = sparql.queryAndConvert()
    # print(ret)
    for r in ret["results"]["bindings"]:
        print(r)
except Exception as e:
    print(e)
# %%
