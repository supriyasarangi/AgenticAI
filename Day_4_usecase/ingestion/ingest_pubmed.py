"""
One-time seeding script for PubMed literature into Chroma.

Run with: python -m ingestion.ingest_pubmed

Fetches abstracts from seed queries, chunks them, embeds them,
and upserts into the pubmed_literature collection.
"""

import logging
import sys
from datetime import datetime

from ingestion.pubmed_connector import seed_pubmed_ingestion
from ingestion.chunking import chunk_document
from ingestion.embeddings import embed_texts
from ingestion.vector_store import get_chroma_client, get_or_create_collection

logger = logging.getLogger(__name__)


def ingest_pubmed() -> None:
    """
    Main ingestion pipeline: fetch → chunk → embed → upsert.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting PubMed ingestion pipeline...")

    try:
        # Step 1: Fetch abstracts from seed queries
        logger.info("Step 1: Fetching PubMed abstracts from seed queries")
        abstracts = seed_pubmed_ingestion()

        if not abstracts:
            logger.warning("No abstracts fetched. Aborting ingestion.")
            return

        logger.info(f"Fetched {len(abstracts)} abstracts")

        # Step 2: Initialize Chroma client and collection
        logger.info("Step 2: Initializing Chroma vector store")
        client = get_chroma_client()
        collection = get_or_create_collection(
            client,
            "pubmed_literature",
            metadata={"source": "PubMed", "source_type": "literature"},
        )

        # Step 3: Chunk and embed documents
        logger.info("Step 3: Chunking and embedding abstracts")
        all_chunk_ids = []
        all_embeddings = []
        all_documents = []
        all_metadatas = []

        for abstract in abstracts:
            pmid = abstract.get("pmid", "unknown")
            title = abstract.get("title", "")
            text = abstract.get("abstract", "")
            authors = abstract.get("authors", [])
            pub_date = abstract.get("pub_date", "")

            # Chunk the abstract
            chunks = chunk_document(text, pmid, chunk_size=500, overlap=50)

            for chunk in chunks:
                chunk_id = chunk["chunk_id"]
                chunk_text = chunk["text"]

                all_chunk_ids.append(chunk_id)
                all_documents.append(chunk_text)

                # Build metadata for this chunk
                metadata = {
                    "document_id": pmid,
                    "source": "PubMed",
                    "source_type": "literature",
                    "therapeutic_area": "oncology",
                    "jurisdiction": "GLOBAL",
                    "source_authority_tier": 0.75,
                    "title": title,
                    "pmid": pmid,
                    "authors": ", ".join(authors) if authors else "",
                    "pub_date": pub_date,
                    "char_span_start": chunk["char_span_start"],
                    "char_span_end": chunk["char_span_end"],
                    "doi": "",
                }
                all_metadatas.append(metadata)

        logger.info(f"Created {len(all_chunk_ids)} chunks from {len(abstracts)} abstracts")

        # Step 4: Embed all chunks
        logger.info("Step 4: Generating embeddings")
        all_embeddings = embed_texts(all_documents)

        # Step 5: Upsert into Chroma
        logger.info(f"Step 5: Upserting {len(all_chunk_ids)} chunks into Chroma")
        collection.upsert(
            ids=all_chunk_ids,
            embeddings=all_embeddings,
            documents=all_documents,
            metadatas=all_metadatas,
        )

        # Verify ingestion
        collection_count = collection.count()
        logger.info(f"PubMed collection now contains {collection_count} chunks")

        logger.info("✓ PubMed ingestion complete!")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    ingest_pubmed()
