FROM python:3.10.5
WORKDIR /dnd-bot
RUN pip install pipenv
RUN ls -hal
ADD . /dnd-bot
ADD .git/ ./.git/
RUN ls -hal /
RUN ls -hal /dnd-bot
RUN pipenv install --deploy
CMD [ "pipenv", "run", "python3", "bot.py" ]