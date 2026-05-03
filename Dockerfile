FROM python:3.11-slim

WORKDIR /app

COPY requirments.txt .

RUN pip install --no-cache-dir -r requirments.txt

COPY . .

CMD ["sh", "-c", "if [ ! -f nord_challenge.db ]; then python main.py; fi && uvicorn app.api:app --host 0.0.0.0 --port 8000"]