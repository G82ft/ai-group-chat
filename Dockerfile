FROM python:3.12-alpine3.19

WORKDIR /app
VOLUME ["/app/data", "/app/config"]
ADD . .
RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "main.py"]
