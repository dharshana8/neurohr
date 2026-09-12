import re
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.ai import HRPolicyDocument

class PolicyRAGService:
    @staticmethod
    def chunk_text(text: str, chunk_size_words: int = 200, overlap_words: int = 40) -> List[str]:
        """
        Split policy text into overlapping sliding-window word chunks.
        """
        words = text.split()
        if not words:
            return []

        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size_words])
            chunks.append(chunk)
            i += (chunk_size_words - overlap_words)
            if i >= len(words) and len(chunks) > 1:
                break
        return chunks

    @staticmethod
    async def index_document(
        org_id,
        title: str,
        content: str,
        category: str = "General Policy"
    ) -> HRPolicyDocument:
        """
        Chunk and store an HR Policy document strictly within the organization scope.
        """
        chunks = PolicyRAGService.chunk_text(content)
        org_ref = org_id.to_ref() if hasattr(org_id, "to_ref") else org_id

        doc = HRPolicyDocument(
            organization_id=org_ref,
            title=title.strip(),
            category=category.strip(),
            content=content.strip(),
            chunks=chunks
        )
        await doc.insert()
        return doc

    @staticmethod
    async def search_relevant_chunks(
        org_id,
        query: str,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant policy chunks strictly within the tenant's organization_id.
        Uses TF-IDF cosine similarity matching across chunks.
        """
        # Strictly tenant-scoped query
        docs = await HRPolicyDocument.find({"organization_id.$id": org_id}).to_list()
        if not docs:
            return []

        all_chunks: List[Tuple[str, str]] = []  # (doc_title, chunk_text)
        corpus: List[str] = []

        for doc in docs:
            for ch in doc.chunks:
                all_chunks.append((doc.title, ch))
                corpus.append(ch)

        if not corpus:
            return []

        # Build TF-IDF vector space
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            query_vec = vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        except Exception:
            # Fallback to simple keyword match if vocabulary is empty
            similarities = np.array([sum(1 for w in query.lower().split() if w in c.lower()) for c in corpus])

        # Get top matching chunk indices
        ranked_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in ranked_indices:
            score = float(similarities[idx])
            if score > 0.05:  # Relevance threshold
                title, chunk_text = all_chunks[idx]
                results.append({
                    "title": title,
                    "chunk": chunk_text,
                    "score": round(score, 3)
                })

        return results

    @staticmethod
    def format_chunks_for_prompt(results: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into clean markdown citations for Grok.
        """
        if not results:
            return "No relevant organization policy excerpts found."

        formatted = []
        for i, item in enumerate(results, 1):
            formatted.append(f"--- Excerpt {i} [Source: {item['title']}] ---\n{item['chunk']}")
        return "\n\n".join(formatted)
