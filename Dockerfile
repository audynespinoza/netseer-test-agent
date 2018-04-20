#docker run   --name='agent1.end2end.phx'   --rm   --hostname='agent1.end2end.phx'   -e AGENT_ENV=dev   -e API_URL_HOST='http://netseerapi'   -e PASSWORD=eb7cv8kx0rggpzhcwhawclxc4m2xcfgu   -e AGENT_NAME=agent1.end2end.phx   --network=netseer  --memory=2G   --memory-swap=2g audynespinoza/netseer-test-agent:latest

# FROM directive instructing base image to build upon
FROM python:3.6

ENV DOCKER_CONTAINER=1

# Add requirements.txt
RUN mkdir -p /agent
ADD requirements.txt /agent
ADD requirements.txt /

# Install app requirements
RUN pip install -r requirements.txt

# Create app directory
ADD ./code /agent

# Set the default directory for our environment
WORKDIR /agent

RUN chmod 755 /agent/netseer_test_agent.py

CMD ["python3", "/agent/netseer_test_agent.py"]
