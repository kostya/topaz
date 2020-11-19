FROM ubuntu:18.04

RUN apt-get update && apt-get install -y git python python-pip wget curl openssl vim libffi-dev bzip2 pkg-config make gcc \
  && rm -rf /var/lib/apt/lists/* /tmp/* /usr/share/man/*

RUN cd /opt && git clone https://github.com/kostya/topaz.git && cd topaz \
  && pip install -r requirements.txt

RUN cd /opt \
  && curl -L 'https://downloads.python.org/pypy/pypy2.7-v7.3.2-linux64.tar.bz2' > l.tar.bz2 \
  && tar xjf l.tar.bz2 \
  && curl -L 'https://downloads.python.org/pypy/pypy2.7-v7.3.2-src.tar.bz2' > s.tar.bz2 \
  && tar xjf s.tar.bz2 \
  && rm *.tar.bz2

ENV PYTHONPATH="/opt/pypy2.7-v7.3.2-src:/usr/local/lib/python2.7/dist-packages"
ENV PATH="/opt/pypy2.7-v7.3.2-linux64/bin:/opt/pypy2.7-v7.3.2-src/rpython/bin/:${PATH}"

RUN cd /opt/topaz && pypy ../pypy2.7-v7.3.2-src/rpython/bin/rpython -Ojit targettopaz.py \
  && rm -rf /tmp/*

ENV PATH="/opt/topaz/bin:${PATH}"

WORKDIR /opt/topaz
