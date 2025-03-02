FROM python:3-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	python3-dev \
	libpq-dev \
	bash \
	iputils-ping \
	openssh-client \
	sshpass \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY  . .

RUN chmod +x BashGetInfo.sh
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "./backend.py"]