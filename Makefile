Container_list =  $(shell docker ps -aq)
Image_list = $(shell docker images -aq)
Volume_list = $(shell docker volume ls -q)
Network_list = $(shell docker network ls -q)

MAGENTA=\033[0;35m
CYAN=\033[0;36m  
BLUE=\033[0;34m
RED=\033[0;31m
GREEN=\033[0;32m
NC=\033[0m # No Color


build:
	docker compose up --build -d

up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down --volumes --rmi all

# psql -h localhost -U postgres -d server_db

restart:
	docker compose restart

all: build

cclean:
	if [ -n "$(Container_list)" ]; then docker stop $(Container_list); fi
	if [ -n "$(Container_list)" ]; then docker rm $(Container_list); fi
	if [ -n "$(Image_list)" ]; then docker rmi $(Image_list); fi
	if [ -n "$(Volume_list)" ]; then docker volume rm $(Volume_list); fi
	if [ -n "$(Network_list)" ]; then docker network rm $(Network_list); fi


prune: cclean
	yes | docker system prune -a --volumes --force --filter "until=24h"
	yes | docker volume prune --force --filter "until=24h"
	rm -rf /home/$(USER)/data

test:
	if [ -n "$(list)" ]; then \
		echo "hello"; \
	fi

logs-nginx:
	@echo "\t${MAGENTA}Nginx${NC}"
	docker logs nginx

logs-db:
	@echo "\t${MAGENTA}Postgres${NC}"
	docker logs postgres

logs-DataCollection:
	@echo "\t${MAGENTA}DataCollection${NC}"
	docker logs DataCollection

logs-API:
	@echo "\t${MAGENTA}API${NC}"
	docker logs API

logs-Frontend:
	@echo "\t${MAGENTA}Frontend${NC}"
	docker logs Frontend

logs: logs-db logs-DataCollection logs-API logs-Frontend


rebuild: clean build run

# Debugging and utility targets

debug:
	docker compose up

logs-follow:
	docker compose logs -f

ps:
	docker compose ps

status:
	docker ps -a

restart-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Please specify SERVICE, e.g., make restart-service SERVICE=Frontend"; \
		exit 1; \
	else \
		docker compose restart $(SERVICE); \
	fi

rebuild-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Please specify SERVICE, e.g., make rebuild-service SERVICE=Frontend"; \
		exit 1; \
	else \
		docker compose up --build -d $(SERVICE); \
	fi

shell:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Please specify SERVICE, e.g., make shell SERVICE=Frontend"; \
		exit 1; \
	else \
		docker exec -it $(SERVICE) /bin/bash; \
	fi