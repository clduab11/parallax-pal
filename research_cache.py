#!/usr/bin/env python3
"""
Research Cache - Handles caching of research queries and results
Provides efficient caching mechanisms for research operations with proper
invalidation, TTL management, and serialization.
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchCache:
    """File-based caching system for research queries and results"""
    
    def __init__(self, cache_dir: str = None, ttl: int = 86400, max_size: int = 100):
        """Initialize research cache
        
        Args:
            cache_dir: Directory to store cache files (default: ./cache/research)
            ttl: Default time-to-live in seconds (default: 24 hours)
            max_size: Maximum number of cache entries (default: 100)
        """
        # Set up cache directory
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = os.path.join(os.getcwd(), "cache", "research")
            
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set cache parameters
        self.default_ttl = ttl
        self.max_size = max_size
        
        # Load cache index to track entries
        self.cache_index = self._load_cache_index()
        
        # Clean up stale entries on initialization
        self._cleanup_stale_entries()
    
    def _generate_cache_key(self, query: str, **metadata) -> str:
        """Generate a cache key based on query and metadata
        
        Args:
            query: Research query string
            metadata: Additional metadata to include in key generation
            
        Returns:
            str: Hex digest of the hash
        """
        # Build a key string combining query and key metadata
        key_parts = [query.strip().lower()]
        
        # Add relevant metadata to key
        if 'model' in metadata:
            key_parts.append(str(metadata['model']))
            
        if 'continuous_mode' in metadata:
            key_parts.append(f"continuous:{metadata['continuous_mode']}")
        
        # Create hash of combined key parts
        key_string = "||".join(key_parts)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get the file path for a cache key
        
        Args:
            cache_key: Cache key string
            
        Returns:
            str: Absolute path to cache file
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_cache_index(self) -> Dict[str, Dict[str, Any]]:
        """Load the cache index from disk
        
        Returns:
            Dict containing cache key -> metadata mapping
        """
        index_path = os.path.join(self.cache_dir, "index.json")
        
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading cache index: {str(e)}")
                # Return empty index if file is corrupted
                return {}
        
        # Return empty index if file doesn't exist
        return {}
    
    def _save_cache_index(self) -> None:
        """Save the cache index to disk"""
        index_path = os.path.join(self.cache_dir, "index.json")
        
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"Error saving cache index: {str(e)}")
    
    def _cleanup_stale_entries(self) -> None:
        """Remove stale entries from cache based on TTL"""
        current_time = time.time()
        stale_keys = []
        
        # Find stale entries
        for key, metadata in list(self.cache_index.items()):
            # Skip if no expiry time or not accessible
            if 'expiry_time' not in metadata:
                continue
                
            # Check if entry is expired
            if metadata['expiry_time'] < current_time:
                stale_keys.append(key)
        
        # Remove stale entries
        for key in stale_keys:
            self._remove_cache_entry(key)
        
        # Log cleanup results
        if stale_keys:
            logger.info(f"Cleaned up {len(stale_keys)} stale cache entries")
    
    def _enforce_size_limit(self) -> None:
        """Enforce the cache size limit by removing oldest entries"""
        if len(self.cache_index) <= self.max_size:
            return
            
        # Sort entries by access time (oldest first)
        entries = [(k, v.get('last_access', 0)) for k, v in self.cache_index.items()]
        entries.sort(key=lambda x: x[1])
        
        # Remove oldest entries until we're under the limit
        entries_to_remove = entries[:len(entries) - self.max_size]
        
        for key, _ in entries_to_remove:
            self._remove_cache_entry(key)
            
        logger.info(f"Removed {len(entries_to_remove)} old cache entries to enforce size limit")
    
    def _remove_cache_entry(self, cache_key: str) -> None:
        """Remove a cache entry
        
        Args:
            cache_key: Cache key to remove
        """
        # Remove from index
        if cache_key in self.cache_index:
            del self.cache_index[cache_key]
            
        # Remove file if it exists
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except OSError as e:
                logger.error(f"Error removing cache file {cache_path}: {str(e)}")
    
    def get(self, query: str, **metadata) -> Optional[Dict[str, Any]]:
        """Get cached research result for a query
        
        Args:
            query: Research query string
            metadata: Additional metadata for cache key generation
            
        Returns:
            Dict containing cached research result or None if not found/expired
        """
        # Generate cache key
        cache_key = self._generate_cache_key(query, **metadata)
        cache_path = self._get_cache_path(cache_key)
        
        # Check if entry exists in index
        if cache_key not in self.cache_index:
            return None
            
        # Check if cache file exists
        if not os.path.exists(cache_path):
            # Remove from index if file doesn't exist
            self._remove_cache_entry(cache_key)
            self._save_cache_index()
            return None
            
        # Check if entry is expired
        current_time = time.time()
        if 'expiry_time' in self.cache_index[cache_key] and self.cache_index[cache_key]['expiry_time'] < current_time:
            # Remove expired entry
            self._remove_cache_entry(cache_key)
            self._save_cache_index()
            return None
            
        try:
            # Load cached data
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
                # Update access time
                self.cache_index[cache_key]['last_access'] = current_time
                self._save_cache_index()
                
                logger.info(f"Cache hit for query: {query[:50]}{'...' if len(query) > 50 else ''}")
                return cache_data
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading cache file {cache_path}: {str(e)}")
            # Remove corrupt entry
            self._remove_cache_entry(cache_key)
            self._save_cache_index()
            return None
    
    def set(self, query: str, data: Dict[str, Any], ttl: int = None, **metadata) -> bool:
        """Cache research result for a query
        
        Args:
            query: Research query string
            data: Data to cache
            ttl: Time-to-live in seconds (default: class default)
            metadata: Additional metadata for cache key generation
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.default_ttl
            
        # Generate cache key
        cache_key = self._generate_cache_key(query, **metadata)
        cache_path = self._get_cache_path(cache_key)
        
        # Calculate expiry time
        current_time = time.time()
        expiry_time = current_time + ttl
        
        try:
            # Save data to cache file
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Update index
            self.cache_index[cache_key] = {
                'query': query,
                'creation_time': current_time,
                'expiry_time': expiry_time,
                'last_access': current_time,
                'metadata': metadata
            }
            
            # Save index
            self._save_cache_index()
            
            # Enforce size limit
            self._enforce_size_limit()
            
            logger.info(f"Cached result for query: {query[:50]}{'...' if len(query) > 50 else ''}")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"Error writing to cache file {cache_path}: {str(e)}")
            return False
    
    def delete(self, query: str, **metadata) -> bool:
        """Delete cached research result for a query
        
        Args:
            query: Research query string
            metadata: Additional metadata for cache key generation
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        # Generate cache key
        cache_key = self._generate_cache_key(query, **metadata)
        
        # Check if entry exists
        if cache_key not in self.cache_index:
            return False
            
        # Remove entry
        self._remove_cache_entry(cache_key)
        self._save_cache_index()
        
        logger.info(f"Deleted cache entry for query: {query[:50]}{'...' if len(query) > 50 else ''}")
        return True
    
    def clear(self) -> bool:
        """Clear all cached research results
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        try:
            # Remove all cache files
            for key in list(self.cache_index.keys()):
                self._remove_cache_entry(key)
                
            # Reset index
            self.cache_index = {}
            self._save_cache_index()
            
            logger.info("Cleared all cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dict containing cache statistics
        """
        # Count total entries
        total_entries = len(self.cache_index)
        
        # Count expired entries
        current_time = time.time()
        expired_entries = sum(1 for meta in self.cache_index.values() 
                            if 'expiry_time' in meta and meta['expiry_time'] < current_time)
        
        # Calculate cache size on disk
        cache_size = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.cache_dir, filename)
                cache_size += os.path.getsize(file_path)
        
        # Get oldest and newest entry times
        creation_times = [meta.get('creation_time', 0) for meta in self.cache_index.values()]
        oldest_entry_time = min(creation_times) if creation_times else 0
        newest_entry_time = max(creation_times) if creation_times else 0
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'cache_size_bytes': cache_size,
            'cache_size_mb': round(cache_size / (1024 * 1024), 2),
            'oldest_entry_time': datetime.fromtimestamp(oldest_entry_time).isoformat() if oldest_entry_time else None,
            'newest_entry_time': datetime.fromtimestamp(newest_entry_time).isoformat() if newest_entry_time else None,
            'cache_dir': self.cache_dir
        }