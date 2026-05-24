FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py vaultx_sites.py ./

CMD ["python", "bot.py"]
