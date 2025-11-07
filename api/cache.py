from typing import Optional
from collections import OrderedDict
from threading import Lock

from climatemaps.geogrid import GeoGrid


class GeoGridCache:
    # NOTE: In-memory caching works correctly with a single uvicorn worker.
    # If using multiple workers (--workers N), each worker has separate memory,
    # which means each worker has its own cache (data may be loaded once per worker).
    MAX_SIZE = 128

    def __init__(self) -> None:
        self._cache: OrderedDict[str, GeoGrid] = OrderedDict()
        self._lock = Lock()

    def _get_cache_key(self, data_type: str, month: int) -> str:
        return f"{data_type}_{month}"

    def get(self, data_type: str, month: int) -> Optional[GeoGrid]:
        cache_key = self._get_cache_key(data_type, month)
        with self._lock:
            return self._cache.get(cache_key)

    def set(self, data_type: str, month: int, geo_grid: GeoGrid) -> None:
        cache_key = self._get_cache_key(data_type, month)
        with self._lock:
            if cache_key not in self._cache and len(self._cache) >= self.MAX_SIZE:
                self._cache.popitem(last=False)
            self._cache[cache_key] = geo_grid
