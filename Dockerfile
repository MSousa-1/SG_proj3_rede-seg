FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nftables tcpdump \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py firewall.sh ./
COPY tests ./tests
ENTRYPOINT ["/bin/sh", "/app/firewall.sh"]
CMD ["python", "/app/app.py"]
