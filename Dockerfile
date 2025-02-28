FROM python:3.12-alpine3.19

WORKDIR /app
VOLUME ["/app/config"]
ADD . .
RUN pip install -r requirements.txt

ENTRYPOINT ["/bin/ash"]
