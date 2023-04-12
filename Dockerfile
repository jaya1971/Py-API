FROM ubuntu:20.04

# Environment variables #################################
ENV DEBIAN_FRONTEND noninteractive
ARG SQLSERVER
ENV SQLSVR=$SQLSERVER
ARG SQLPASS
ENV SQLPW=$SQLPASS
ARG SQLSA
ENV SQLUSER=$SQLSA
ARG SQLSTR
ENV SQLSTRING=$SQLSTR

# Run Updates ##########################################
RUN apt-get update && apt-get install -y software-properties-common gcc && \
    add-apt-repository -y ppa:deadsnakes/ppa \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y python3.10 python3-distutils python3-pip python3-apt \
    net-tools \
    python3-pip \
    curl \
    apt-transport-https \
    inetutils-ping wget nano sudo \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | tee /etc/apt/sources.list.d/msprod.list

RUN apt-get update -y
ENV ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive

RUN apt-get install mssql-tools unixodbc-dev -y \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install pyodbc

WORKDIR /sql
SHELL ["/bin/bash", "-c"] 
COPY bootstrap.sh .
RUN chmod +rwx bootstrap.sh

COPY ./requirements/openssl.cnf /etc/ssl/openssl.cnf

COPY ./requirements/requirements.txt .
RUN pip install -r requirements.txt

COPY ./src ./src

# ssh install and configure ###############################################################################
RUN apt update && apt install  openssh-server sudo -y \
    && useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 devops \
    && mkdir -p /run/sshd && echo "devops:Docker!" | chpasswd
COPY sshd_config /etc/ssh/
RUN service ssh start

# Expose ports on container ###############################################################################
EXPOSE 80 2222

CMD ["/usr/sbin/sshd","-D"]
ENTRYPOINT ["python3", "./src/main.py", "--host=0.0.0.0", "--port=80"]