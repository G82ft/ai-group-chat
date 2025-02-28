FROM python:3.12-alpine3.19

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "main.py"]
