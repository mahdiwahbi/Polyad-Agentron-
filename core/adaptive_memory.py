from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime
import numpy as np

from utils.logger import logger

class AdaptiveMemory:
    """
    Adaptive memory system with token management and optimization
    """
    def __init__(self, max_tokens: int = 300):
        self.max_tokens = max_tokens
        self.memory_buffer = []
        self.token_usage = 0
        self.importance_threshold = 0.5
        self.memory_file = 'data/memory.json'
        
    def add_memory(self, content: Dict[str, Any], importance: float = 0.5) -> bool:
        """Add new memory with importance score"""
        try:
            # Calculate token count
            token_count = self._estimate_tokens(content)
            
            # Check if we need to free up space
            if self.token_usage + token_count > self.max_tokens:
                self._optimize_memory(token_count)
                
            # Only add if important enough
            if importance >= self.importance_threshold:
                memory_entry = {
                    'content': content,
                    'importance': importance,
                    'tokens': token_count,
                    'created_at': datetime.now().isoformat(),
                    'access_count': 0
                }
                
                self.memory_buffer.append(memory_entry)
                self.token_usage += token_count
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return False
            
    def get_memory(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve relevant memories"""
        try:
            # Calculate relevance scores
            scored_memories = []
            for memory in self.memory_buffer:
                score = self._calculate_relevance(memory['content'], query)
                if score > 0:
                    scored_memories.append((score, memory))
                    memory['access_count'] += 1
                    
            # Sort by relevance
            scored_memories.sort(reverse=True, key=lambda x: x[0])
            
            # Return top relevant memories
            return [memory for _, memory in scored_memories[:5]]
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
            
    def _optimize_memory(self, required_tokens: int):
        """Optimize memory usage by removing less important entries"""
        try:
            while self.token_usage + required_tokens > self.max_tokens:
                if not self.memory_buffer:
                    break
                    
                # Calculate scores for removal
                removal_scores = []
                for i, memory in enumerate(self.memory_buffer):
                    score = self._calculate_removal_score(memory)
                    removal_scores.append((score, i))
                    
                # Remove lowest scoring memory
                removal_scores.sort()
                idx_to_remove = removal_scores[0][1]
                removed_memory = self.memory_buffer.pop(idx_to_remove)
                self.token_usage -= removed_memory['tokens']
                
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            
    def _calculate_removal_score(self, memory: Dict[str, Any]) -> float:
        """Calculate score for memory removal"""
        age = (datetime.now() - datetime.fromisoformat(memory['created_at'])).total_seconds()
        
        # Factors:
        # - Higher importance = higher score (keep)
        # - More recent = higher score (keep)
        # - More accesses = higher score (keep)
        score = (
            memory['importance'] * 0.4 +
            (1.0 / (age + 1)) * 0.3 +
            (memory['access_count'] / 100) * 0.3
        )
        
        return score
        
    def _calculate_relevance(self, memory_content: Dict[str, Any], query: Dict[str, Any]) -> float:
        """Calculate relevance score between memory and query"""
        try:
            # Convert both to sets of items
            memory_items = set(str(item) for item in self._flatten_dict(memory_content).items())
            query_items = set(str(item) for item in self._flatten_dict(query).items())
            
            # Calculate Jaccard similarity
            intersection = len(memory_items.intersection(query_items))
            union = len(memory_items.union(query_items))
            
            return intersection / union if union > 0 else 0
            
        except Exception as e:
            logger.error(f"Relevance calculation failed: {e}")
            return 0
            
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
        
    def _estimate_tokens(self, content: Dict[str, Any]) -> int:
        """Estimate token count for content"""
        # Simple estimation: characters / 4
        return len(json.dumps(content)) // 4
        
    async def save_state(self):
        """Save memory state to file"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'max_tokens': self.max_tokens,
                    'token_usage': self.token_usage,
                    'importance_threshold': self.importance_threshold,
                    'memory_buffer': self.memory_buffer
                }, f)
                
        except Exception as e:
            logger.error(f"Failed to save memory state: {e}")
            
    async def load_state(self):
        """Load memory state from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    state = json.load(f)
                    self.max_tokens = state['max_tokens']
                    self.token_usage = state['token_usage']
                    self.importance_threshold = state['importance_threshold']
                    self.memory_buffer = state['memory_buffer']
                    
        except Exception as e:
            logger.error(f"Failed to load memory state: {e}")
            
    def clear(self):
        """Clear all memories"""
        self.memory_buffer = []
        self.token_usage = 0
        
    @property
    def stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'total_memories': len(self.memory_buffer),
            'token_usage': self.token_usage,
            'max_tokens': self.max_tokens,
            'usage_percent': (self.token_usage / self.max_tokens) * 100 if self.max_tokens > 0 else 0,
            'importance_threshold': self.importance_threshold
        }
