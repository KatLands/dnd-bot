start:
	sudo docker-compose up -d

stop:
	sudo docker-compose down

logs:
	sudo docker-compose logs

mongo:
	sudo docker exec -it dnd-bot-mongo-1 mongosh
