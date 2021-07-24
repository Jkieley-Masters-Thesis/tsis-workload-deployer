FROM python:3.8.10-alpine3.13

WORKDIR /app

ADD ./requirements.txt /app/requirements.txt
ADD ./asu-ssh-config/jkieley_asu /app/jkieley_asu
ADD ./asu-ssh-config/ssh-config.txt /app/ssh-config.txt
ADD ./asu-ssh-config/prepare-config.sh /app/prepare-config.sh

RUN apk add --update --no-cache openssh
RUN apk add --update --no-cache bash

RUN mkdir /root/.ssh
#RUN echo '127.0.0.1 jamesk-kubernetes-master' >> /etc/hosts

RUN PATH_TO_SSH_KEY=/app/jkieley_asu SRC_FILE=/app/ssh-config.txt OUTPUT_FILE=/root/.ssh/config bash -c '/app/prepare-config.sh'
RUN chmod 400 /app/jkieley_asu

RUN pip install -r requirements.txt

COPY . /app

RUN chmod +x /app/entrypoint-deployer.sh
RUN cp /app/config/known_hosts /root/.ssh/

ENV FROM_CLUSTER_KUBE_CONFIG_FILE=/app/config/asu-on-prem-config
ENV SAVEDI_JOB_YAML=/app/config/deployment_yamls/savedi_job.yaml
ENV ARPUT_JOB_YAML=/app/config/deployment_yamls/arput_job.yaml
ENV ARPUI_JOB_YAML=/app/config/deployment_yamls/arpui_job.yaml
ENV SAVEDT_JOB_YAML=/app/config/deployment_yamls/savedt_job.yaml
ENV CFDWID_LR_TRAIN_JOB_YAML=/app/config/deployment_yamls/cfdwid_lr_train_job.yaml
ENV CFDWID_LR_INFERENCE_JOB_YAML=/app/config/deployment_yamls/cfdwid_lr_inference_job.yaml


ENTRYPOINT /app/entrypoint-deployer.sh