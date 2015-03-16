FROM ubuntu

RUN apt-get update
RUN apt-get install curl -y
RUN curl -L https://opscode.com/chef/install.sh | bash
ADD chef/berks-cookbooks /cookbooks
RUN chef-client -z -r "recipe[python]"

ADD flask/flask_app.py /opt/
EXPOSE 5000

CMD ["python3.3", "/opt/flask_app.py"]
