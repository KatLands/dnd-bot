FROM python:3.10.5
RUN pip install pipenv
COPY . /dnd-bot
WORKDIR /dnd-bot
RUN pipenv install --deploy
ENTRYPOINT /bin/bash
#CMD [ "pipenv", "run", "python3", "bot.py" ]