# wiki-retrieval
"wiki-retrieval" is a document retrieval service that utilizes Wikipedia as its primary data source and is designed to be fully compatible with the OpenAI chatgpt-retrieval-plugin API.

Here are some features:

1. The service has been developed using [Sanic](https://github.com/sanic-org/sanic), leveraging its `Worker-Pool` and `Signal` features for handling relatively unpredictable processing performance, as opposed to using [FastAPI](https://github.com/tiangolo/fastapi).
2. The API interface remains consistent with the OpenAI chatgpt-retrieval-plugins, maintaining easy integration.
3. The data sourcing employs a lazy-loading approach. If a search result does not meet the criteria, a background process is triggered that searches Wikipedia, following which the documents are inserted into the retrieval database.

# Quick Started

The service is designed with containerization in mind, making it easy to get started.

```shell
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
docker-compose up -d
```

You can then query the service using the API:

```python
import requests
from rich import print

url = "http://localhost:8990/query"
query_body = {"queries": [{"top_k": 3, "query": "why rainbow colored?"}]}
res = requests.post(url, json=query_body)
print(res.json())
```

Here is an example of the kind of search results you can expect:

```json
{
    'results': [
        {
            'query': 'why rainbow colored?',
            'results': [
                {
                    'score': 0.8450728058815002,
                    'embedding': None,
                    'text': 'A rainbow flag is a multicolored flag consisting of the colors of the rainbow. The designs differ, but many of
the colors are based on the spectral colors of the visible light spectrum.The LGBT flag introduced in 1978 is the most recognized use of a
rainbow flag.\n\n\n== History ==\nIn the 18th century, American Revolutionary War writer Thomas Paine proposed that a rainbow flag be used
as a maritime flag to signify neutral ships in time of war.Contemporary international uses of a rainbow flag dates to the beginning of the
20th century. The International Co-operative Alliance adopted a rainbow flag in 1925.',
                    'id': 'b563c41e-2c06-48f2-9ee6-5248ae87f962',
                    'metadata': {
                        'created_at': '2023-06-21T10:03:18.951962',
                        'title': 'Rainbow flag',
                        'lang': 'en',
                        'source': 'wiki',
                        'name': 'Rainbow flag'
                    }
                },
                {
                    'score': 0.8320353627204895,
                    'embedding': None,
                    'text': 'The rainbow flag, also known as the gay pride flag or simply pride flag, is a symbol of lesbian, gay,
bisexual, and transgender (LGBT) pride and LGBT social movements. The colors reflect the diversity of the LGBT community and the spectrum
of human sexuality and gender. Using a rainbow flag as a symbol of gay pride began in San Francisco, California, but eventually became
common at LGBT rights events worldwide.\nOriginally devised by artist Gilbert Baker, Lynn Segerblom, James McNamara and other activists,
the design underwent several revisions after its debut in 1978, and continues to inspire variations.',
                    'id': 'e5571597-2e40-439b-8f87-fe1890580a28',
                    'metadata': {
                        'created_at': '2023-06-21T10:03:18.951962',
                        'title': 'Rainbow flag (LGBT)',
                        'lang': 'en',
                        'source': 'wiki',
                        'name': 'Rainbow flag (LGBT)'
                    }
                },
                {
                    'score': 0.8183635473251343,
                    'embedding': None,
                    'text': 'for colored girls who have considered suicide / when the rainbow is enuf is a 1976 work by Ntozake Shange. It
consists of a series of poetic monologues to be accompanied by dance movements and music, a form which Shange coined the word choreopoem to
describe. for colored girls... tells the stories of seven women who have suffered oppression in a racist and sexist society.As a
choreopoem, the piece is a series of 20 separate poems choreographed to music that weaves interconnected stories of love, empowerment,
struggle and loss into a complex representation of sisterhood.',
                    'id': 'd5266237-3553-4138-acba-ddb1102b650d',
                    'metadata': {
                        'created_at': '2023-06-21T10:03:18.951962',
                        'title': 'For Colored Girls Who Have Considered Suicide / When the Rainbow Is Enuf',
                        'lang': 'en',
                        'source': 'wiki',
                        'name': 'For Colored Girls Who Have Considered Suicide / When the Rainbow Is Enuf'
                    }
                }
            ]
        }
    ]
}
```