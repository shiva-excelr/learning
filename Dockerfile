FROM ubuntu:latest
# FROM rasa/rasa:2.8.0
FROM python:3.8.11
# RUN apt-get update -y && \
#     apt-get install -y python-pip python-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
# ADD ./models /app/models/
# ADD ./actions /app/actions/
# ADD ./scripts /app/scripts/
RUN pip install -r requirements.txt
RUN echo "AA"
RUN pip uninstall tensorflow
RUN echo "bb"
COPY . /app

EXPOSE 5000
ENTRYPOINT []


CMD bash /app/scripts/start_services.sh
CMD [ "web_app.py" ]