"""
SPARQL access to the official parliamentary open data.

Both chambers publish their sitting calendars and member registers as linked
data. That replaces two fragile pieces of scraping: Camera's month-by-month
crawl (which stepped back in 30-day hops and therefore skipped months) and
Senato's single un-paginated listing page (which capped coverage at whatever
fitted on one screen).

The queries below are pinned against the live endpoints. Notes that cost time to
discover, recorded so nobody has to rediscover them:

  * dati.senato.it answers 403 without a browser-ish User-Agent.
  * `osr:legislatura` is an xsd:integer - filtering on the string "19" silently
    matches nothing.
  * Camera assembly sittings are the `seduta.rdf/s19_<n>` URIs; the
    `BF_19_...` ones are bulletins, not assembly sittings.
  * Camera dates are plain YYYYMMDD strings; Senate dates are xsd:date.
"""

import json
import logging
import urllib.parse
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

CAMERA_ENDPOINT = "https://dati.camera.it/sparql"
SENATO_ENDPOINT = "https://dati.senato.it/sparql"

SPARQL_USER_AGENT = (
    "Mozilla/5.0 (compatible; ParliamentSpeechAnalyzer/1.0; +research; "
    "contact: via repository)"
)

CAMERA_LEGISLATURE_URI = "http://dati.camera.it/ocd/legislatura.rdf/repubblica_{leg}"


class SparqlError(Exception):
    """The endpoint refused or failed to answer."""


class SparqlClient:
    """Minimal SPARQL-over-HTTP client returning plain dict rows."""

    def __init__(self, endpoint: str, timeout: int = 90):
        self.endpoint = endpoint
        self.timeout = timeout

    def select(self, query: str) -> list[dict]:
        """Run a SELECT and return `[{var: value}]` with values as strings."""
        url = self.endpoint + "?" + urllib.parse.urlencode({
            'query': query,
            'format': 'application/sparql-results+json',
        })
        request = urllib.request.Request(url, headers={
            'Accept': 'application/sparql-results+json',
            'User-Agent': SPARQL_USER_AGENT,
        })

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            raise SparqlError(f"{self.endpoint}: {e}") from e

        return [
            {name: binding['value'] for name, binding in row.items()}
            for row in payload['results']['bindings']
        ]


# =============================================================================
# QUERIES
# =============================================================================

CAMERA_SESSIONS = """
PREFIX ocd: <http://dati.camera.it/ocd/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?seduta ?date ?label WHERE {{
  ?seduta a ocd:seduta ;
          ocd:rif_leg <{legislature_uri}> ;
          dc:date ?date ;
          rdfs:label ?label .
  FILTER (CONTAINS(STR(?seduta), "seduta.rdf/s{leg}_"))
  FILTER (?date >= "{since}")
}}
ORDER BY DESC(?date)
"""

CAMERA_ROSTER = """
PREFIX ocd: <http://dati.camera.it/ocd/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?deputato ?cognome ?nome ?gruppo ?fine WHERE {{
  ?deputato a ocd:deputato ;
            ocd:rif_leg <{legislature_uri}> ;
            foaf:surname ?cognome ;
            foaf:firstName ?nome .
  OPTIONAL {{
    ?deputato ocd:aderisce ?adesione .
    ?adesione rdfs:label ?gruppo .
    OPTIONAL {{ ?adesione ocd:motivoTermine ?fine }}
  }}
}}
"""

SENATO_SESSIONS = """
PREFIX osr: <http://dati.senato.it/osr/>
SELECT ?seduta ?data ?numero WHERE {{
  ?seduta a osr:SedutaAssemblea ;
          osr:legislatura {leg} ;
          osr:dataSeduta ?data ;
          osr:numeroSeduta ?numero .
  FILTER (?data >= "{since}"^^<http://www.w3.org/2001/XMLSchema#date>)
}}
ORDER BY DESC(?data)
"""

SENATO_ROSTER = """
PREFIX osr: <http://dati.senato.it/osr/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT DISTINCT ?senatore ?cognome ?nome WHERE {{
  ?senatore a osr:Senatore ;
            foaf:lastName ?cognome ;
            foaf:firstName ?nome ;
            osr:mandato ?mandato .
  ?mandato osr:legislatura {leg} .
}}
"""

# Ground truth for "who spoke in which sitting" - lets a run measure how well
# speaker attribution from the HTML matched the official record.
SENATO_INTERVENTIONS = """
PREFIX osr: <http://dati.senato.it/osr/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?seduta ?cognome ?nome WHERE {{
  ?senatore osr:interviene ?intervento ;
            foaf:lastName ?cognome ;
            foaf:firstName ?nome .
  ?intervento osr:seduta ?seduta .
  ?seduta a osr:SedutaAssemblea ; osr:legislatura {leg} ; osr:dataSeduta ?data .
  FILTER (?data >= "{since}"^^<http://www.w3.org/2001/XMLSchema#date>)
}}
"""


def camera_client(timeout: int = 90) -> SparqlClient:
    return SparqlClient(CAMERA_ENDPOINT, timeout=timeout)


def senato_client(timeout: int = 90) -> SparqlClient:
    return SparqlClient(SENATO_ENDPOINT, timeout=timeout)


def legislature_uri(legislature: int) -> str:
    return CAMERA_LEGISLATURE_URI.format(leg=legislature)
