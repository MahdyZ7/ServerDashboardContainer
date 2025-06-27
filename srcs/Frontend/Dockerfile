FROM python:3-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade dash dash-core-components dash-html-components dash-table
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "Dash.py"]