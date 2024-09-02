# Make syz-build;
FROM golang:1.21.6-bookworm as syzbuild
WORKDIR /
RUN apt update && apt install git -y
RUN git clone https://github.com/google/syzkaller.git
WORKDIR /syzkaller
RUN make syz-build

# Kernel building environment;
FROM gcr.io/syzkaller/syzbot:latest
WORKDIR /
RUN mkdir /KBDr
COPY --from=syzbuild /syzkaller/bin/syz-build /usr/local/bin/syz-build

# Install pip;
RUN apt install python3-pip python3-venv tar gzip -y -q
RUN python3 -m venv venv

# Install kworker & kbuilder;
WORKDIR /KBDr
COPY ./kworker /KBDr/kworker
COPY ./kbuilder /KBDr/kbuilder
WORKDIR /KBDr/kworker
RUN /venv/bin/pip install .
WORKDIR /KBDr/kbuilder
RUN /venv/bin/pip install .

# Run
WORKDIR /root
ENTRYPOINT ["/venv/bin/python3", "-m", "KBDr.kbuilder"]
