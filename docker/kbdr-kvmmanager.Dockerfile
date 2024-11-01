FROM golang:1.23.1-bookworm as syzbuild

WORKDIR /
RUN apt update && apt install git -y && git clone https://github.com/kaloronahuang/syzkaller.git
WORKDIR /syzkaller
RUN make all && make crush

FROM python:3.11-bookworm

# Essential tools;
RUN apt update && apt install git make -y

# syz-crush;
COPY --from=syzbuild /syzkaller/bin/syz-crush /usr/local/bin/syz-crush

WORKDIR /root

# Install Golang toolchain;
RUN wget "https://dl.google.com/go/go1.23.1.linux-amd64.tar.gz" -O go.tar.gz && tar -C /usr/local -xzf go.tar.gz
ENV GOROOT=/usr/local/go
ENV PATH=$GOROOT/bin:$PATH

# Prepare a base syzkaller repo;
RUN git clone https://github.com/kaloronahuang/syzkaller.git

# kvmmanager;
COPY ./kworker /KBDr/kworker
COPY ./kvmmanager /KBDr/kvmmanager

WORKDIR /KBDr/kworker
RUN pip install .
WORKDIR /KBDr/kvmmanager
RUN pip install .

WORKDIR /root
ENTRYPOINT ["/usr/local/bin/python3", "-m", "KBDr.kvmmanager"]
