from typing import Optional
import time

class MemoryCache:
    def __init__(self):
        print("🧠 Initializing Enterprise Memory Cache Mock...")
        self.cache = {}
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[dict]:
        if key in self.cache:
            self.hits += 1
            print(f"⚡ CACHE HIT [{self.hits}]: {key[:30]}...")
            return self.cache[key]
        self.misses += 1
        return None
        
    def set(self, key: str, value: dict):
        self.cache[key] = value

# Singleton instance
memory_cache = MemoryCache()
