FROM registry.access.redhat.com/ubi8/python-36

ENV SPARK_VERSION=2.4.5
ENV HADOOP_VERSION=2.7

WORKDIR /app

COPY Pipfile* /app/

## NOTE - rhel enforces user container permissions stronger ##
USER root

RUN yum -y install python3-pip wget

RUN wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
      && tar -xvzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
      && mv spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} spark \
      && rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
      && cd /

RUN yum -y install java-1.8.0-openjdk

RUN pip install --upgrade pip \
  && pip install --upgrade pipenv \
  && pipenv install --system --deploy

USER 1001

COPY . /app
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--env", "DJANGO_SETTINGS_MODULE=pythondjangoapp.settings.development", "pythondjangoapp.wsgi", "--timeout 120"]
