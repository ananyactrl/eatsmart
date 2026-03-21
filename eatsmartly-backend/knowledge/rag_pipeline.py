"""
RAG (Retrieval-Augmented Generation) Pipeline for EatSmartly.

Embeds regulatory documents (FSSAI PDFs, EFSA opinions, IFCT data) into a
vector store for retrieval, then uses an LLM to generate source-cited
explanations.

Architecture:
  1. Document Loader — reads PDFs, CSVs, regulatory text
  2. Chunker — splits into meaningful chunks with metadata
  3. Embedder — converts chunks to vectors (uses sentence-transformers or Gemini)
  4. Vector Store — stores and retrieves vectors (local JSON-based for MVP)
  5. LLM Explainer — uses Gemini to generate plain-language explanations from context
"""
import json
import os
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class DocumentChunk:
    """A chunk of text from a regulatory document."""
    chunk_id: str
    text: str
    source_file: str
    source_title: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Don't serialize the embedding to JSON (too large)
        d.pop("embedding", None)
        return d


@dataclass
class RetrievalResult:
    """A result from the vector store retrieval."""
    chunk: DocumentChunk
    score: float  # Similarity score (0-1, higher = more relevant)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.chunk.text,
            "source": self.chunk.source_title,
            "page": self.chunk.page_number,
            "section": self.chunk.section,
            "score": round(self.score, 4),
        }


# ---------------------------------------------------------------------------
# Document Loader
# ---------------------------------------------------------------------------

class DocumentLoader:
    """Load and chunk regulatory documents."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_pdf(self, pdf_path: str, source_title: str = "") -> List[DocumentChunk]:
        """Load a PDF and split into chunks."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
            return []

        chunks = []
        title = source_title or Path(pdf_path).stem

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text or len(text.strip()) < 20:
                        continue

                    page_chunks = self._chunk_text(
                        text=text,
                        source_file=pdf_path,
                        source_title=title,
                        page_number=page_num,
                    )
                    chunks.extend(page_chunks)

            logger.info(f"Loaded {len(chunks)} chunks from {pdf_path}")
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {e}")

        return chunks

    def load_text(self, text: str, source_title: str, source_file: str = "inline") -> List[DocumentChunk]:
        """Load plain text and split into chunks."""
        return self._chunk_text(text, source_file, source_title)

    def load_regulatory_kb(self) -> List[DocumentChunk]:
        """
        Load the built-in regulatory knowledge base as chunks for RAG.
        This makes our structured data searchable via vector similarity.
        """
        from knowledge.regulatory_db import INGREDIENT_DATABASE, IngredientInfo

        chunks = []
        seen = set()

        for info in INGREDIENT_DATABASE.values():
            if info.name in seen:
                continue
            seen.add(info.name)

            # Create a rich text representation for embedding
            text_parts = [
                f"Ingredient: {info.name}",
                f"Also known as: {', '.join(info.aliases)}" if info.aliases else "",
                f"Category: {info.category.value}",
                f"E-Number: {info.e_number}" if info.e_number else "",
                f"Description: {info.description}" if info.description else "",
                f"Concern Level: {info.concern_level.value}",
                f"Summary: {info.concern_summary}" if info.concern_summary else "",
                f"ADI: {info.adi}" if info.adi else "",
            ]

            # Add regulatory info
            for reg in info.regulatory:
                reg_text = f"{reg.body.value}: {reg.status.value}"
                if reg.max_limit:
                    reg_text += f" (limit: {reg.max_limit})"
                text_parts.append(reg_text)

            # Add health effects
            if info.health_effects:
                text_parts.append("Health effects: " + "; ".join(info.health_effects))

            text = "\n".join(p for p in text_parts if p)

            chunk_id = hashlib.md5(f"kb_{info.name}".encode()).hexdigest()[:12]
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                text=text,
                source_file="regulatory_knowledge_base",
                source_title="EatSmartly Regulatory Database",
                section=info.name,
                metadata={
                    "ingredient_name": info.name,
                    "category": info.category.value,
                    "concern_level": info.concern_level.value,
                },
            ))

        logger.info(f"Loaded {len(chunks)} chunks from regulatory knowledge base")
        return chunks

    def _chunk_text(
        self,
        text: str,
        source_file: str,
        source_title: str,
        page_number: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """Split text into overlapping chunks."""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= self.chunk_size:
            chunk_id = hashlib.md5(f"{source_file}_{page_number}_{text[:50]}".encode()).hexdigest()[:12]
            return [DocumentChunk(
                chunk_id=chunk_id,
                text=text,
                source_file=source_file,
                source_title=source_title,
                page_number=page_number,
            )]

        chunks = []
        # Split on sentence boundaries where possible
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunk_id = hashlib.md5(
                    f"{source_file}_{page_number}_{len(chunks)}_{current_chunk[:50]}".encode()
                ).hexdigest()[:12]
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    text=current_chunk.strip(),
                    source_file=source_file,
                    source_title=source_title,
                    page_number=page_number,
                ))
                # Overlap: keep last part
                words = current_chunk.split()
                overlap_words = words[-min(self.chunk_overlap, len(words)):]
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk.strip():
            chunk_id = hashlib.md5(
                f"{source_file}_{page_number}_{len(chunks)}_{current_chunk[:50]}".encode()
            ).hexdigest()[:12]
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                text=current_chunk.strip(),
                source_file=source_file,
                source_title=source_title,
                page_number=page_number,
            ))

        return chunks


# ---------------------------------------------------------------------------
# Vector Store (Local JSON-based for MVP, upgrade to FAISS/Pinecone later)
# ---------------------------------------------------------------------------

class LocalVectorStore:
    """
    Simple local vector store using cosine similarity.
    Good enough for MVP with <10,000 chunks.
    Upgrade path: FAISS, Pinecone, Chroma, or Weaviate.
    """

    def __init__(self, store_path: str = None):
        self.store_path = store_path or os.path.join(
            os.path.dirname(__file__), '..', 'data', 'vector_store.json'
        )
        self.chunks: List[DocumentChunk] = []
        self.embeddings: List[List[float]] = []
        self._loaded = False

    def add_chunks(self, chunks: List[DocumentChunk]):
        """Add chunks with their embeddings to the store."""
        for chunk in chunks:
            if chunk.embedding:
                self.chunks.append(chunk)
                self.embeddings.append(chunk.embedding)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[RetrievalResult]:
        """Search for most similar chunks to a query embedding."""
        if not self.embeddings:
            return []

        scores = []
        for i, emb in enumerate(self.embeddings):
            score = self._cosine_similarity(query_embedding, emb)
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            results.append(RetrievalResult(
                chunk=self.chunks[idx],
                score=score,
            ))

        return results

    def save(self):
        """Save the store to disk."""
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        data = {
            "chunks": [c.to_dict() for c in self.chunks],
            "embeddings": self.embeddings,
        }
        with open(self.store_path, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved {len(self.chunks)} chunks to {self.store_path}")

    def load(self):
        """Load the store from disk."""
        if not os.path.exists(self.store_path):
            logger.warning(f"Vector store not found at {self.store_path}")
            return

        with open(self.store_path, 'r') as f:
            data = json.load(f)

        self.chunks = [
            DocumentChunk(**{k: v for k, v in c.items()})
            for c in data.get("chunks", [])
        ]
        self.embeddings = data.get("embeddings", [])
        self._loaded = True
        logger.info(f"Loaded {len(self.chunks)} chunks from {self.store_path}")

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @property
    def size(self) -> int:
        return len(self.chunks)


# ---------------------------------------------------------------------------
# Embedder (using sentence-transformers or TF-IDF fallback)
# ---------------------------------------------------------------------------

class Embedder:
    """
    Text embedder for the RAG pipeline.

    Primary: sentence-transformers (all-MiniLM-L6-v2 — 384 dims, fast, free)
    Fallback: TF-IDF vectors (no model download needed)
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.use_tfidf = False
        self.tfidf_vectorizer = None
        self._init_model()

    def _init_model(self):
        """Try to load sentence-transformers, fall back to TF-IDF."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence-transformer model: {self.model_name}")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. Using TF-IDF fallback. "
                "Install with: pip install sentence-transformers"
            )
            self.use_tfidf = True
        except Exception as e:
            logger.warning(f"Could not load sentence-transformer: {e}. Using TF-IDF fallback.")
            self.use_tfidf = True

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        if self.model:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            return self._tfidf_embed(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts at once (more efficient)."""
        if self.model:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [e.tolist() for e in embeddings]
        else:
            # Fit (or refit) the TF-IDF on this corpus for much better results
            return self._tfidf_embed_batch(texts)

    def _tfidf_embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Fit TF-IDF on the full corpus and return embeddings. Much better than per-document."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        logger.info(f"Fitting TF-IDF on {len(texts)} documents...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=512,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            max_df=0.95,
        )
        matrix = self.tfidf_vectorizer.fit_transform(texts)
        self._tfidf_fitted_on_corpus = True
        # Save vectorizer for later query embedding
        import pickle
        vec_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tfidf_vectorizer.pkl')
        os.makedirs(os.path.dirname(vec_path), exist_ok=True)
        with open(vec_path, 'wb') as f:
            pickle.dump(self.tfidf_vectorizer, f)
        logger.info(f"TF-IDF vectorizer saved ({len(self.tfidf_vectorizer.vocabulary_)} terms)")
        return [row.toarray()[0].tolist() for row in matrix]

    def _tfidf_embed(self, text: str) -> List[float]:
        """TF-IDF embedding for a single query text."""
        if self.tfidf_vectorizer is None:
            # Try to load saved vectorizer
            import pickle
            vec_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tfidf_vectorizer.pkl')
            if os.path.exists(vec_path):
                with open(vec_path, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
                logger.info("Loaded saved TF-IDF vectorizer")
            else:
                # Last-resort fallback with basic vocabulary
                from sklearn.feature_extraction.text import TfidfVectorizer
                self.tfidf_vectorizer = TfidfVectorizer(max_features=512)
                self.tfidf_vectorizer.fit([
                    "food additive preservative colorant sweetener emulsifier stabilizer thickener antioxidant",
                    "fssai fda efsa codex approved banned restricted limit regulation permitted",
                    "sodium sugar salt fat protein carbohydrate fiber calcium iron vitamin",
                    "cancer carcinogenic tumor health risk safety concern toxic",
                    "allergy allergen reaction sensitivity intolerance gluten soy milk",
                    "artificial natural organic synthetic processed refined fortified",
                    "maximum level permitted concentration ppm mg kg body weight day",
                    "beverage bread biscuit chocolate ice cream noodles chips snack",
                ])

        vec = self.tfidf_vectorizer.transform([text]).toarray()[0]
        return vec.tolist()


# ---------------------------------------------------------------------------
# RAG Pipeline
# ---------------------------------------------------------------------------

class RAGPipeline:
    """
    Full RAG pipeline: embed documents → store → retrieve → explain.
    """

    def __init__(self, store_path: str = None):
        self.loader = DocumentLoader()
        self.store = LocalVectorStore(store_path)
        self.embedder = None  # Lazy-init to avoid loading model on import
        self._initialized = False

    def _ensure_embedder(self):
        """Lazy-initialize the embedder."""
        if self.embedder is None:
            self.embedder = Embedder()

    def index_documents(self, pdf_paths: List[str] = None, include_kb: bool = True):
        """
        Index documents into the vector store.

        Args:
            pdf_paths: List of PDF file paths to index
            include_kb: Whether to include the built-in regulatory KB
        """
        self._ensure_embedder()
        all_chunks = []

        # Load built-in knowledge base
        if include_kb:
            kb_chunks = self.loader.load_regulatory_kb()
            all_chunks.extend(kb_chunks)

        # Load PDFs
        if pdf_paths:
            for path in pdf_paths:
                if os.path.exists(path):
                    chunks = self.loader.load_pdf(path, Path(path).stem)
                    all_chunks.extend(chunks)
                else:
                    logger.warning(f"PDF not found: {path}")

        if not all_chunks:
            logger.warning("No chunks to index")
            return

        # Embed all chunks
        logger.info(f"Embedding {len(all_chunks)} chunks...")
        texts = [c.text for c in all_chunks]
        embeddings = self.embedder.embed_texts(texts)

        for chunk, embedding in zip(all_chunks, embeddings):
            chunk.embedding = embedding

        # Store
        self.store.add_chunks(all_chunks)
        self.store.save()
        self._initialized = True
        logger.info(f"Indexed {len(all_chunks)} chunks into vector store")

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Retrieve most relevant chunks for a query."""
        self._ensure_embedder()

        if not self.store.size:
            self.store.load()

        if not self.store.size:
            logger.warning("Vector store is empty. Run index_documents first.")
            return []

        query_embedding = self.embedder.embed_text(query)
        return self.store.search(query_embedding, top_k=top_k)

    def explain_ingredient(self, ingredient_name: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Use RAG to generate source-cited explanation for an ingredient.

        Returns context from the vector store. LLM explanation can be added
        by calling Gemini separately with this context.
        """
        results = self.retrieve(ingredient_name, top_k=top_k)

        if not results:
            return {
                "ingredient": ingredient_name,
                "found": False,
                "context": [],
                "message": "No relevant information found in our document store.",
            }

        context = []
        for r in results:
            context.append({
                "text": r.chunk.text,
                "source": r.chunk.source_title,
                "page": r.chunk.page_number,
                "relevance": round(r.score, 3),
            })

        return {
            "ingredient": ingredient_name,
            "found": True,
            "context": context,
            "message": f"Found {len(context)} relevant passages from regulatory documents.",
        }

    @property
    def is_ready(self) -> bool:
        """Check if the pipeline is ready for queries."""
        if not self.store.size:
            self.store.load()
        return self.store.size > 0
