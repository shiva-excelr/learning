FROM ubuntu:latest

FROM python:3.8
RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
# ADD ./models /app/models/
# ADD ./actions /app/actions/
# ADD ./scripts /app/scripts/
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000
ENTRYPOINT []

CMD [ "web_app.py" ]
CMD bash /app/scripts/start_services.sh