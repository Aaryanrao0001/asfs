"""
Semantic deduplication using embeddings and cosine similarity.

Identifies semantically similar clips and keeps only
the highest-scoring variant.
"""

import logging
from typing import Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Try importing sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available - semantic deduplication disabled")


class SemanticDeduplicator:
    """
    Removes semantically duplicate clips using embedding similarity.
    """
    
    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        similarity_threshold: float = 0.85
    ):
        """
        Initialize semantic deduplicator.
        
        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Cosine similarity threshold for duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.model = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading sentence transformer model: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info("Semantic deduplicator initialized")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
                logger.warning("Semantic deduplication will be disabled")
        else:
            logger.info("Semantic deduplicator initialized (disabled - no model)")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def embed_clips(self, clips: List[Dict]) -> List[np.ndarray]:
        """
        Generate embeddings for clip texts.
        
        Args:
            clips: List of clips with 'text' field
            
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            # Return empty embeddings if model not available
            return [np.array([]) for _ in clips]
        
        texts = [clip.get('text', '') for clip in clips]
        
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [np.array([]) for _ in clips]
    
    def find_duplicates(
        self,
        clips: List[Dict],
        embeddings: List[np.ndarray] = None
    ) -> List[List[int]]:
        """
        Find groups of duplicate clips.
        
        Args:
            clips: List of clips
            embeddings: Pre-computed embeddings (optional)
            
        Returns:
            List of duplicate groups (each group is list of indices)
        """
        if self.model is None:
            logger.debug("Semantic deduplication skipped (no model)")
            return []
        
        # Generate embeddings if not provided
        if embeddings is None:
            embeddings = self.embed_clips(clips)
        
        # Find similar pairs
        n = len(clips)
        duplicate_groups = []
        processed = set()
        
        for i in range(n):
            if i in processed:
                continue
            
            group = [i]
            
            for j in range(i + 1, n):
                if j in processed:
                    continue
                
                # Check if embeddings are valid
                if len(embeddings[i]) == 0 or len(embeddings[j]) == 0:
                    continue
                
                similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                
                if similarity >= self.similarity_threshold:
                    group.append(j)
                    processed.add(j)
            
            if len(group) > 1:
                duplicate_groups.append(group)
                processed.add(i)
        
        return duplicate_groups
    
    def deduplicate_clips(
        self,
        clips: List[Dict],
        score_key: str = 'psychological_score'
    ) -> List[Dict]:
        """
        Remove duplicate clips, keeping highest scoring variant.
        
        Args:
            clips: List of clips to deduplicate
            score_key: Key to use for ranking duplicates
            
        Returns:
            Deduplicated list of clips
        """
        if self.model is None:
            logger.info("Semantic deduplication skipped (model not available)")
            return clips
        
        if not clips:
            return []
        
        # Generate embeddings
        embeddings = self.embed_clips(clips)
        
        # Find duplicate groups
        duplicate_groups = self.find_duplicates(clips, embeddings)
        
        if not duplicate_groups:
            logger.info("No semantic duplicates found")
            return clips
        
        # Keep highest scoring clip from each group
        indices_to_remove = set()
        
        for group in duplicate_groups:
            # Sort group by score
            group_with_scores = [
                (idx, clips[idx].get(score_key, 0)) for idx in group
            ]
            group_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Keep first (highest scoring), remove rest
            best_idx = group_with_scores[0][0]
            best_score = group_with_scores[0][1]
            
            for idx, score in group_with_scores[1:]:
                indices_to_remove.add(idx)
                logger.debug(
                    f"Removing duplicate clip at {clips[idx].get('start', 0):.1f}s "
                    f"(score={score:.1f}) - keeping clip at "
                    f"{clips[best_idx].get('start', 0):.1f}s (score={best_score:.1f})"
                )
        
        # Filter clips
        deduplicated = [
            clip for i, clip in enumerate(clips) if i not in indices_to_remove
        ]
        
        logger.info(
            f"Semantic deduplication: removed {len(indices_to_remove)} clips, "
            f"{len(deduplicated)} remaining"
        )
        
        return deduplicated
    
    def analyze_similarity_matrix(self, clips: List[Dict]) -> Dict:
        """
        Analyze similarity between all clips (for debugging/analysis).
        
        Args:
            clips: List of clips
            
        Returns:
            Dictionary with similarity statistics
        """
        if self.model is None:
            return {'error': 'Model not available'}
        
        embeddings = self.embed_clips(clips)
        n = len(clips)
        
        similarities = []
        for i in range(n):
            for j in range(i + 1, n):
                if len(embeddings[i]) > 0 and len(embeddings[j]) > 0:
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append(sim)
        
        if not similarities:
            return {'error': 'No valid similarities computed'}
        
        return {
            'clip_count': n,
            'comparison_count': len(similarities),
            'avg_similarity': float(np.mean(similarities)),
            'max_similarity': float(np.max(similarities)),
            'min_similarity': float(np.min(similarities)),
            'duplicates_at_threshold': sum(1 for s in similarities if s >= self.similarity_threshold)
        }
