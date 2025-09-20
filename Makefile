Container_list =  $(shell docker ps -aq)
Image_list = $(shell docker images -aq)
Volume_list = $(shell docker volume ls -q)
Network_list = $(shell docker network ls -q)

MAGENTA=\033[0;35m
YELLOW=\033[0;33m
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
	docker compose down --rmi all

# psql -h localhost -U postgres -d server_db

restart:
	docker compose restart

all: build

cclean:
	docker compose down --volumes --rmi all

prune: cclean
	if [ -n "$(Container_list)" ]; then docker stop $(Container_list); fi
	if [ -n "$(Container_list)" ]; then docker rm $(Container_list); fi
	if [ -n "$(Image_list)" ]; then docker rmi $(Image_list); fi
	if [ -n "$(Volume_list)" ]; then docker volume rm $(Volume_list); fi
	if [ -n "$(Network_list)" ]; then docker network rm $(Network_list); fi
	yes | docker system prune -a --volumes --force --filter "until=24h"
	yes | docker volume prune --force --filter "until=24h"
	rm -rf /home/$(USER)/data

test:
	if [ -n "$(list)" ]; then \
		echo "hello"; \
	fi

logs-nginx:
	@echo -e "\t${MAGENTA}=== Nginx Logs ===${NC}"
	docker logs nginx

logs-nginx-tail:
	@echo -e "\t${MAGENTA}=== Nginx Logs (Last 50 lines) ===${NC}"
	docker logs --tail=50 nginx

logs-db:
	@echo -e "\t${MAGENTA}=== Postgres Logs ===${NC}"
	docker logs postgres

logs-db-tail:
	@echo -e "\t${MAGENTA}=== Postgres Logs (Last 50 lines) ===${NC}"
	docker logs --tail=50 postgres

logs-DataCollection:
	@echo -e "\t${MAGENTA}=== DataCollection Logs ===${NC}"
	docker logs DataCollection

logs-DataCollection-tail:
	@echo -e "\t${MAGENTA}=== DataCollection Logs (Last 50 lines) ===${NC}"
	docker logs --tail=50 DataCollection

logs-API:
	@echo -e "\t${MAGENTA}=== API Logs ===${NC}"
	docker logs API

logs-API-tail:
	@echo -e "\t${MAGENTA}=== API Logs (Last 50 lines) ===${NC}"
	docker logs --tail=50 API

logs-Frontend:
	@echo -e "\t${MAGENTA}=== Frontend Logs ===${NC}"
	docker logs Frontend

logs-Frontend-tail:
	@echo -e "\t${MAGENTA}=== Frontend Logs (Last 50 lines) ===${NC}"
	docker logs --tail=50 Frontend

logs: logs-nginx-tail logs-db-tail logs-DataCollection-tail logs-API-tail logs-Frontend-tail

logs-all: logs-nginx logs-db logs-DataCollection logs-API logs-Frontend


rebuild: clean build

# Debugging and utility targets

debug:
	docker compose up

logs-follow:
	@echo -e "${CYAN}Following all container logs in real-time (Ctrl+C to exit)${NC}"
	docker compose logs -f

logs-follow-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo -e "${RED}Please specify SERVICE, e.g., make logs-follow-service SERVICE=DataCollection${NC}"; \
		exit 1; \
	else \
		echo -e "${CYAN}Following $(SERVICE) logs in real-time (Ctrl+C to exit)${NC}"; \
		docker logs -f $(SERVICE); \
	fi

logs-errors:
	@echo -e "${RED}=== Error Logs from All Services ===${NC}"
	@echo -e "${CYAN}Checking nginx logs...${NC}"
	@docker logs nginx 2>&1 | grep -i error || echo "No nginx errors found"
	@echo -e "\n${CYAN}Checking postgres logs...${NC}"
	@docker logs postgres 2>&1 | grep -i error || echo "No postgres errors found"
	@echo -e "\n${CYAN}Checking DataCollection logs...${NC}"
	@docker logs DataCollection 2>&1 | grep -i error || echo "No DataCollection errors found"
	@echo -e "\n${CYAN}Checking API logs...${NC}"
	@docker logs API 2>&1 | grep -i error || echo "No API errors found"
	@echo -e "\n${CYAN}Checking Frontend logs...${NC}"
	@docker logs --timestamps Frontend 2>&1 | grep -i error || echo "No Frontend errors found"

logs-since:
	@if [ -z "$(TIME)" ]; then \
		echo -e "${RED}Please specify TIME, e.g., make logs-since TIME=1h${NC}"; \
		echo -e "${BLUE}Examples: TIME=5m (5 minutes), TIME=1h (1 hour), TIME=2024-01-01${NC}"; \
		exit 1; \
	else \
		echo -e "${CYAN}Logs since $(TIME) ago${NC}"; \
		docker compose logs --since=$(TIME) --timestamps; \
	fi

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

health:
	@echo -e "${CYAN}Service Health Status:${NC}"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

cleanup-data:
	@echo -e "${YELLOW}Running data retention cleanup (removing data older than 3 months)...${NC}"
	docker exec DataCollection /bin/bash -c "CLEANUP_ONLY=true python backend.py"

db-stats:
	@echo -e "${CYAN}Database Statistics:${NC}"
	@docker exec -it postgres psql -U postgres -d server_db -c "\
	SELECT 'server_metrics' as table_name, COUNT(*) as total_records, \
	       MIN(timestamp) as oldest_record, MAX(timestamp) as newest_record \
	FROM server_metrics \
	UNION ALL \
	SELECT 'top_users' as table_name, COUNT(*) as total_records, \
	       MIN(timestamp) as oldest_record, MAX(timestamp) as newest_record \
	FROM top_users;"

# Single execution commands (for testing scheduled mode)
collect-once:
	@echo -e "${GREEN}Running single data collection cycle...${NC}"
	docker exec DataCollection /bin/bash -c "EXECUTION_MODE=scheduled python backend.py"

collect-once-with-disk:
	@echo -e "${GREEN}Running single data collection cycle with disk usage...${NC}"
	docker exec DataCollection /bin/bash -c "EXECUTION_MODE=scheduled COLLECT_DISK_USAGE=true python backend.py"

collect-once-with-cleanup:
	@echo -e "${GREEN}Running single data collection cycle with cleanup...${NC}"
	docker exec DataCollection /bin/bash -c "EXECUTION_MODE=scheduled RUN_CLEANUP=true python backend.py"

# Cron management (for scheduled mode)
show-cron:
	@echo -e "${CYAN}Current crontab entries:${NC}"
	docker exec DataCollection crontab -l

cron-logs:
	@echo -e "${CYAN}DataCollection cron logs:${NC}"
	docker exec DataCollection tail -50 /var/log/datacollection.log

cron-logs-follow:
	@echo -e "${CYAN}Following DataCollection cron logs (Ctrl+C to exit):${NC}"
	docker exec DataCollection tail -f /var/log/datacollection.log