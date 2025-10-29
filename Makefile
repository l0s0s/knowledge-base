.PHONY: up down test migrate shell create-superuser

up:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from example..."; \
		cp .env.example .env 2>/dev/null || true; \
	fi
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

test:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from example..."; \
		cp .env.example .env 2>/dev/null || true; \
	fi
	@if ! docker-compose ps | grep -q "web.*Up"; then \
		echo "Services are not running. Starting services..."; \
		docker-compose up -d; \
		echo "Waiting for services to be ready..."; \
		sleep 10; \
	fi
	docker-compose exec web python manage.py test

test-local:
	python manage.py test

migrate:
	@if ! docker-compose ps | grep -q "web.*Up"; then \
		echo "Services are not running. Starting services..."; \
		docker-compose up -d; \
		sleep 10; \
	fi
	docker-compose exec web python manage.py migrate

makemigrations:
	@if ! docker-compose ps | grep -q "web.*Up"; then \
		echo "Services are not running. Starting services..."; \
		docker-compose up -d; \
		sleep 10; \
	fi
	docker-compose exec web python manage.py makemigrations

shell:
	@if ! docker-compose ps | grep -q "web.*Up"; then \
		echo "Services are not running. Starting services..."; \
		docker-compose up -d; \
		sleep 10; \
	fi
	docker-compose exec web python manage.py shell

create-superuser:
	@if ! docker-compose ps | grep -q "web.*Up"; then \
		echo "Services are not running. Starting services..."; \
		docker-compose up -d; \
		sleep 10; \
	fi
	docker-compose exec web python manage.py createsuperuser

logs:
	docker-compose logs -f web

restart:
	docker-compose restart web

setup:
	cp .env.example .env
	docker-compose build
	docker-compose up -d
	sleep 5
	docker-compose exec web python manage.py migrate
	docker-compose exec web python manage.py createsuperuser || true
