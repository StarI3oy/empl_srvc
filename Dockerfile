FROM python:3.11.5-alpine


# ENV ENV_URL=${ENV_URL}
# ENV REACT_APP_API_URL=${API_URL}
# ENV REACT_APP_URL=${APP_URL}
# 

COPY . .
# 
RUN pip install --no-cache-dir --upgrade -r requirements.txt



EXPOSE "8000"
# 
CMD ["fastapi", "run", "main.py", "--port", "8000"]