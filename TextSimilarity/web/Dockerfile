FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install --no-cache-dir ./en_core_web_sm-1.2.0.tar.gz
CMD ["python", "app.py"]
