FROM codeforafrica/gazeti-api:3.0.3

CMD ["celery", "-A", "aleph.queues", "-c", "2", "-l", "INFO", "worker", \
     "--pidfile", "/tmp/celery.pid", "-E"]
