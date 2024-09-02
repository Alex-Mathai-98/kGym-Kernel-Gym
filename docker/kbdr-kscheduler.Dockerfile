FROM python:3.11-alpine

COPY ./kscheduler /KBDr/kscheduler
WORKDIR /KBDr/kscheduler
RUN pip install .
WORKDIR /root
ENTRYPOINT ["/usr/local/bin/python3", "-m", "KBDr.kscheduler"]
