FROM python
COPY . /dnd-bot
WORKDIR /dnd-bot
RUN pip3 install -r requirements.txt
#ENTRYPOINT [ "python3" ]
CMD [ "python3", "bot.py" ]
