"""
PubMed connector — fetch abstracts from NCBI Entrez for drug discovery RAG.

Uses Bio.Entrez to search and fetch PubMed abstracts with seed queries.
Wrapped with network_retry for flaky NCBI calls.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET

from Bio import Entrez

from orchestration.retry import network_retry

logger = logging.getLogger(__name__)

# Seed queries for initial PubMed ingestion (small, representative sample)
SEED_QUERIES = [
    "metastatic melanoma immunotherapy",
    "CAR-T cell therapy leukemia",
]

# NCBI Entrez requires a contact email for rate-limit courtesy
ENTREZ_EMAIL = os.getenv("PUBMED_CONTACT_EMAIL", "user@example.com")


@network_retry
def fetch_pubmed_abstracts(
    query: str,
    retmax: int = 8,
) -> List[Dict[str, Any]]:
    """
    Fetch PubMed abstracts for a given query using Entrez.

    Args:
        query: PubMed search query string
        retmax: Maximum number of results to fetch (default 8)

    Returns:
        List of dicts with pmid, title, abstract, authors, pub_date
    """
    Entrez.email = ENTREZ_EMAIL

    try:
        # Search for matching PMIDs
        logger.info(f"Searching PubMed for: {query}")
        search_handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=retmax,
            sort="relevance",
        )
        search_result = Entrez.read(search_handle)
        search_handle.close()

        pmids = search_result.get("IdList", [])
        logger.info(f"Found {len(pmids)} results for query: {query}")

        if not pmids:
            return []

        # Fetch full records
        logger.info(f"Fetching abstracts for {len(pmids)} PMIDs")
        fetch_handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="xml",
        )
        fetch_result = fetch_handle.read()
        fetch_handle.close()

        # Parse XML and extract abstracts
        abstracts = _parse_pubmed_xml(fetch_result.decode("utf-8"))
        logger.info(f"Parsed {len(abstracts)} abstracts")

        return abstracts

    except Exception as e:
        logger.error(f"Error fetching PubMed abstracts: {e}")
        raise


def _parse_pubmed_xml(xml_string: str) -> List[Dict[str, Any]]:
    """
    Parse PubMed XML response and extract article data.

    Args:
        xml_string: XML response from Entrez.efetch

    Returns:
        List of article dicts
    """
    abstracts = []

    try:
        root = ET.fromstring(xml_string)

        for article in root.findall(".//PubmedArticle"):
            # Extract PMID
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            # Extract title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # Extract abstract
            abstract_elem = article.find(".//AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else ""

            # Extract authors
            authors = []
            for author in article.findall(".//Author"):
                name_elem = author.find("LastName")
                if name_elem is not None:
                    authors.append(name_elem.text)

            # Extract publication date
            pub_date_elem = article.find(".//PubDate/Year")
            pub_date = pub_date_elem.text if pub_date_elem is not None else None

            if title and abstract:  # Only include if both title and abstract present
                abstracts.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "pub_date": pub_date,
                })

    except ET.ParseError as e:
        logger.error(f"Error parsing PubMed XML: {e}")

    return abstracts


def seed_pubmed_ingestion() -> List[Dict[str, Any]]:
    """
    Run the seeding process: fetch from seed queries and return all abstracts.

    Returns:
        Combined list of abstracts from all seed queries
    """
    all_abstracts = []

    for query in SEED_QUERIES:
        try:
            abstracts = fetch_pubmed_abstracts(query, retmax=8)
            all_abstracts.extend(abstracts)
            logger.info(f"Fetched {len(abstracts)} abstracts for seed query: {query}")
        except Exception as e:
            logger.error(f"Failed to fetch for query '{query}': {e}")

    logger.info(f"Total abstracts fetched: {len(all_abstracts)}")
    return all_abstracts
