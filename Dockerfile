FROM python:3.12-alpine3.19

WORKDIR /app
ADD . .
VOLUME ["/app/data", "/app/config"]
RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "main.py"]
