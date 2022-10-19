FROM python:3.10.5
RUN pip install pipenv
RUN pwd
RUN ls -halman
ADD . /dnd-bot
#ADD ./.git /dnd-bot
RUN pwd
RUN ls -hal /
RUN ls -hal /dnd-bot
WORKDIR /dnd-bot
RUN pipenv install --deploy
CMD [ "pipenv", "run", "python3", "bot.py" ]