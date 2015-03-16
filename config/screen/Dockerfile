FROM ubuntu

RUN apt-get update
RUN apt-get install curl -y
RUN curl -L https://opscode.com/chef/install.sh | bash
ADD chef/berks-cookbooks /cookbooks

ADD screen/index.js /opt/
ADD screen/package.json /opt/

RUN chef-client -z -r "recipe[node]"

EXPOSE 3000

CMD ["nodejs", "/opt/index.js"]
