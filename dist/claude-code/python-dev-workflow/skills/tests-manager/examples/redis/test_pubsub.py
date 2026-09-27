"""Example: Redis pub/sub tests -- channel subscribe, pattern subscribe."""

import threading
import time

class TestPubSub:
    def test_publish_subscribe(self, redis_client):
        received_messages: list[str] = []
        channel = "test_channel"

        def subscriber():
            pubsub = redis_client.pubsub()
            pubsub.subscribe(channel)
            for message in pubsub.listen():
                if message["type"] == "message":
                    received_messages.append(message["data"])
                    if len(received_messages) >= 3:
                        break
            pubsub.close()

        sub_thread = threading.Thread(target=subscriber)
        sub_thread.start()
        time.sleep(0.1)  # allow subscriber to connect

        for i in range(3):
            redis_client.publish(channel, f"message_{i}")

        sub_thread.join(timeout=2)
        assert received_messages == ["message_0", "message_1", "message_2"]

    def test_pattern_subscribe(self, redis_client):
        received: list[dict[str, str]] = []

        def subscriber():
            pubsub = redis_client.pubsub()
            pubsub.psubscribe("events:*")
            count = 0
            for message in pubsub.listen():
                if message["type"] == "pmessage":
                    received.append({
                        "channel": message["channel"],
                        "data": message["data"],
                    })
                    count += 1
                    if count >= 2:
                        break
            pubsub.close()

        sub_thread = threading.Thread(target=subscriber)
        sub_thread.start()
        time.sleep(0.1)

        redis_client.publish("events:user:created", "user_1")
        redis_client.publish("events:order:placed", "order_1")

        sub_thread.join(timeout=2)
        assert len(received) == 2
        assert received[0]["channel"] == "events:user:created"
