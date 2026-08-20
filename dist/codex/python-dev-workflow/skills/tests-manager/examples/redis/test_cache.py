"""Example: Redis cache service tests -- CRUD, TTL, increment, hash ops, concurrency."""

import threading

class TestCacheService:
    def test_set_and_get(self, cache_service):
        cache_service.set("test_key", "test_value")
        result = cache_service.get("test_key")
        assert result == "test_value"

    def test_set_with_ttl(self, cache_service, redis_client):
        cache_service.set("ttl_key", "value", ttl=60)
        ttl = redis_client.ttl("ttl_key")
        assert 55 <= ttl <= 60

    def test_get_nonexistent_key(self, cache_service):
        result = cache_service.get("nonexistent")
        assert result is None

    def test_delete(self, cache_service):
        cache_service.set("to_delete", "value")
        cache_service.delete("to_delete")
        assert cache_service.get("to_delete") is None

    def test_increment(self, cache_service):
        cache_service.set("counter", "0")
        result = cache_service.increment("counter")
        assert result == 1
        result = cache_service.increment("counter", amount=5)
        assert result == 6

    def test_hash_operations(self, cache_service):
        cache_service.hset("user:1", mapping={"name": "Alice", "age": "30"})
        result = cache_service.hget("user:1", "name")
        assert result == "Alice"
        all_fields = cache_service.hgetall("user:1")
        assert all_fields == {"name": "Alice", "age": "30"}


class TestCacheConcurrency:
    def test_concurrent_increments(self, redis_client):
        redis_client.set("concurrent_counter", "0")
        increments_per_thread = 100
        num_threads = 10

        def increment_many():
            for _ in range(increments_per_thread):
                redis_client.incr("concurrent_counter")

        threads = [
            threading.Thread(target=increment_many)
            for _ in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final_value = int(redis_client.get("concurrent_counter"))
        assert final_value == num_threads * increments_per_thread
