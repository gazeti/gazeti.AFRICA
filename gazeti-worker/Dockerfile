FROM alephdata/aleph:3.0.3

# boto3/botocore pinned to versions compatible with aleph 3.0.3 dependencies
RUN pip install --no-cache-dir boto3==1.9.243 botocore==1.12.243

# S3 archive path prefix patch (see patches/sitecustomize.py for details)
COPY patches/sitecustomize.py /opt/gazeti-patches/sitecustomize.py
ENV PYTHONPATH=/opt/gazeti-patches

CMD ["celery", "-A", "aleph.queues", "-c", "2", "-l", "INFO", "worker", \
     "--pidfile", "/tmp/celery.pid", "-E"]
