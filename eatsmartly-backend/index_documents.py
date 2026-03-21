"""
Index regulatory PDFs into the RAG vector store.

Usage:
    python index_documents.py              # Index everything
    python index_documents.py --kb-only    # Only index the ingredient KB (fast)
    python index_documents.py --pdfs-only  # Only index the PDFs

This reads FSSAI Compendium + IFCT 2017 PDFs, breaks them into chunks,
generates embeddings, and saves to data/vector_store.json.

After indexing, the decode service can answer questions about ingredients
that aren't in our manual database by searching these documents.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Add parent to path so we can import knowledge module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def find_pdfs() -> dict:
    """Find the regulatory PDF files."""
    base = Path(__file__).resolve().parent.parent  # eatsmart root
    backend = Path(__file__).resolve().parent       # backend root

    pdf_map = {}

    # FSSAI Compendium
    for search_dir in [base, backend, backend / "asset"]:
        fssai = search_dir / "Compendium_Food_Additives_Regulations_20_12_2022.pdf"
        if fssai.exists():
            pdf_map["FSSAI Food Additives Compendium 2022"] = str(fssai)
            break

    # IFCT 2017
    for search_dir in [base, backend, backend / "asset"]:
        ifct = search_dir / "IFCT2017.pdf"
        if ifct.exists():
            pdf_map["Indian Food Composition Tables (IFCT) 2017"] = str(ifct)
            break

    return pdf_map


def main():
    parser = argparse.ArgumentParser(description="Index regulatory documents for RAG")
    parser.add_argument("--kb-only", action="store_true", help="Only index the ingredient knowledge base")
    parser.add_argument("--pdfs-only", action="store_true", help="Only index the PDF documents")
    parser.add_argument("--store-path", type=str, default=None, help="Path to save vector store")
    args = parser.parse_args()

    # Import after path setup
    from knowledge.rag_pipeline import RAGPipeline

    # Import knowledge module to register all ingredients
    import knowledge  # noqa: F401

    store_path = args.store_path
    pipeline = RAGPipeline(store_path=store_path)

    include_kb = not args.pdfs_only
    include_pdfs = not args.kb_only

    pdf_paths = []
    if include_pdfs:
        pdf_map = find_pdfs()
        if pdf_map:
            for title, path in pdf_map.items():
                logger.info(f"Found: {title} -> {path}")
                size_mb = os.path.getsize(path) / (1024 * 1024)
                logger.info(f"  Size: {size_mb:.1f} MB")
                pdf_paths.append(path)
        else:
            logger.warning("No PDF files found! Place FSSAI/IFCT PDFs in the project root or backend/asset/")

    # Start indexing
    start = time.time()
    logger.info("=" * 60)
    logger.info("Starting document indexing...")
    logger.info(f"  Knowledge Base: {'YES' if include_kb else 'NO'}")
    logger.info(f"  PDFs: {len(pdf_paths)} files")
    logger.info("=" * 60)

    pipeline.index_documents(
        pdf_paths=pdf_paths if pdf_paths else None,
        include_kb=include_kb,
    )

    elapsed = time.time() - start
    logger.info("=" * 60)
    logger.info(f"Indexing complete in {elapsed:.1f}s")
    logger.info(f"Total chunks in store: {pipeline.store.size}")
    logger.info(f"Store saved to: {pipeline.store.store_path}")
    logger.info("=" * 60)

    # Quick test
    logger.info("\nQuick retrieval test:")
    test_queries = [
        "tartrazine permitted limit in India",
        "sodium benzoate maximum level beverages",
        "palm oil nutritional composition",
        "iron content of wheat flour",
    ]
    for query in test_queries:
        results = pipeline.retrieve(query, top_k=2)
        if results:
            best = results[0]
            logger.info(f"  Q: {query}")
            logger.info(f"  A: [{best.score:.3f}] {best.chunk.source_title} (p.{best.chunk.page_number}) — {best.chunk.text[:100]}...")
        else:
            logger.info(f"  Q: {query} -> NO RESULTS")
        print()


if __name__ == "__main__":
    main()
