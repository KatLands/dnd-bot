start:
	sudo docker-compose up -d

stop:
	sudo docker-compose down

logs:
	sudo docker-compose logs

redis:
	sudo docker exec -it dnd-bot_redis_1 redis-cli
