FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Tạo thư mục data và set quyền
RUN mkdir -p /app/data && chmod 777 /app/data

CMD ["python", "bot.py"]