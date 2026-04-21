FROM alephdata/aleph:3.0.3

# boto3/botocore pinned to versions compatible with aleph 3.0.3 dependencies
RUN pip install --no-cache-dir boto3==1.9.243 botocore==1.12.243

CMD ["celery", "-A", "aleph.queues", "beat", "-s", "/var/lib/celerybeat-schedule.db"]
