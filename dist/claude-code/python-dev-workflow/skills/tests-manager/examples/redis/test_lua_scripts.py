"""Example: Redis Lua script tests -- rate limiter, atomic transfer."""

class TestLuaScripts:
    def test_rate_limit_script(self, redis_client):
        script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])

        local current = redis.call('INCR', key)
        if current == 1 then
            redis.call('EXPIRE', key, window)
        end

        if current > limit then
            return 0
        else
            return 1
        end
        """
        rate_limit = redis_client.register_script(script)

        for i in range(5):
            result = rate_limit(keys=["ratelimit:user1"], args=[5, 60])
            assert result == 1, f"Request {i + 1} should pass"

        result = rate_limit(keys=["ratelimit:user1"], args=[5, 60])
        assert result == 0, "6th request should be rate limited"

    def test_atomic_transfer_script(self, redis_client):
        script = """
        local from_key = KEYS[1]
        local to_key = KEYS[2]
        local amount = tonumber(ARGV[1])

        local from_balance = tonumber(redis.call('GET', from_key) or 0)
        if from_balance < amount then
            return -1
        end

        redis.call('DECRBY', from_key, amount)
        redis.call('INCRBY', to_key, amount)
        return 1
        """
        transfer = redis_client.register_script(script)

        redis_client.set("balance:alice", "100")
        redis_client.set("balance:bob", "50")

        # Successful transfer
        result = transfer(keys=["balance:alice", "balance:bob"], args=[30])
        assert result == 1
        assert redis_client.get("balance:alice") == "70"
        assert redis_client.get("balance:bob") == "80"

        # Insufficient balance
        result = transfer(keys=["balance:alice", "balance:bob"], args=[100])
        assert result == -1
        assert redis_client.get("balance:alice") == "70"  # unchanged
