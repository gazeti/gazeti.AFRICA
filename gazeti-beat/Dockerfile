FROM codeforafrica/gazeti-api:3.0.3

CMD ["celery", "-A", "aleph.queues", "beat", "-s", "/var/lib/celerybeat-schedule.db"]
