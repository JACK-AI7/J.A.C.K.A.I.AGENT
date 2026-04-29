import redis
from rq import Worker, Queue, Connection

# Configuration for local Redis instance
REDIS_URL = "redis://localhost:6379"

def start_worker():
    """Start a background mission worker."""
    redis_conn = redis.from_url(REDIS_URL)
    with Connection(redis_conn):
        worker = Worker(['jack_missions'])
        print("TITAN Worker: Background Mission Grid Online.")
        worker.work()

if __name__ == "__main__":
    start_worker()
