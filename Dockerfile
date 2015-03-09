FROM ubuntu

RUN apt-get update
RUN apt-get install -y python-pip
RUN pip install flask


ADD flask_app.py /opt/
EXPOSE 5000

CMD ["python", "/opt/flask_app.py"]
