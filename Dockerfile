FROM python:3.11-slim

WORKDIR /app

COPY requirments.txt .

RUN pip install --no-cache-dir -r requirments.txt

COPY . .

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]