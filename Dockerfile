FROM python:3.11.5-alpine

WORKDIR /app
COPY /hdaywidget /app/hdaywidget
COPY /bdaywidget /app/bdaywidget
COPY main.py /app
COPY requirements.txt /app

RUN pip install --no-cache-dir --upgrade -r requirements.txt



EXPOSE "8000"
# 
CMD ["fastapi", "run", "main.py", "--port", "8000"]