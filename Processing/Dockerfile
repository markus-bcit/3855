FROM ubuntu:18.04

LABEL maintainer="mafonso4@my.bcit.ca"
RUN apt-get update -y && apt-get install -y python3 python3-pip
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY . /app
RUN mkdir /data
RUN python3 create_database.py
ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]