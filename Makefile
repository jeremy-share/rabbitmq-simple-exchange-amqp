networks:
	docker network create rabbitmq-simple-exchange-amqp-main || true

up-core:
	make networks
	docker-compose up -d rabbitmq

up-publisher-consumer:
	docker-compose build --pull
	docker-compose up -d simple-publisher simple-consumer

ps:
	docker-compose ps

down:
	docker-compose down

stop:
	make down

logs:
	docker-compose logs -f

logs-publisher-consumer:
	docker-compose logs -f simple-publisher simple-consumer
