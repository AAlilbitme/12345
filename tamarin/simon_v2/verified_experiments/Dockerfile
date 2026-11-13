# add: reproducible environment for the verified experiments.
# Same setup as the server runs: Ubuntu 24.04, Tamarin 1.10.0 (release binary),
# Maude 3.2 from the Ubuntu archive (Tamarin prints "unsupported version 3.2";
# all results in results/ were obtained with exactly this pair).
#
#   docker build -t lightning-tamarin .
#   docker run --rm -it -m 14g lightning-tamarin            # shell in /work
#   docker run --rm -m 14g lightning-tamarin make           # folders 1 and 2 (several hours)
#
# Each goal-2 lemma needs about 10 GB: give the container at least 12 GB.
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl make maude graphviz git \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL -o /tmp/tamarin.tar.gz \
        https://github.com/tamarin-prover/tamarin-prover/releases/download/1.10.0/tamarin-prover-1.10.0-linux64-ubuntu.tar.gz \
    && tar -xzf /tmp/tamarin.tar.gz -C /usr/local/bin tamarin-prover \
    && rm /tmp/tamarin.tar.gz && tamarin-prover --version
ENV LANG=C.UTF-8 MEM=12G LIMIT=3600
WORKDIR /work
COPY . /work
RUN chmod +x /work/*.sh
CMD ["bash"]
