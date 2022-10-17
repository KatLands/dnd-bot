FROM python:3.10.5-slim
RUN pip install pipenv
COPY . /dnd-bot
WORKDIR /dnd-bot
RUN pipenv install --deploy
CMD [ "pipenv", "run", "python3", "bot.py" ]
