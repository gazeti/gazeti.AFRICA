FROM alephdata/aleph:3.0.3

# boto3/botocore pinned to versions compatible with aleph 3.0.3 dependencies
RUN pip install --no-cache-dir boto3==1.9.243 botocore==1.12.243

# S3 archive path prefix patch (see patches/sitecustomize.py for details)
COPY patches/sitecustomize.py /opt/gazeti-patches/sitecustomize.py
ENV PYTHONPATH=/opt/gazeti-patches

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--name", "aleph", \
     "--log-level", "info", "--timeout", "600", "aleph.manage:app"]
