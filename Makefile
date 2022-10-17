start:
	sudo docker-compose up -d

stop:
	sudo docker-compose down

logs:
	sudo docker-compose logs

mongo:
	sudo docker exec -it dnd-bot_mongo_1 mongosh

build:
	docker build -t dragid10/dnd-bot .

run:
	docker run dragid10/dnd-bot

test:
	docker build -t dragid10/dnd-bot . && docker run dragid10/dnd-bot

push-image:
	docker push dragid10/dnd-bot

deploy:
	 flyctl deploy --detach --push --now --no-cache

deploy-status:
	flyctl status