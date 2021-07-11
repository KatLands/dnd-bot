# Discord D&D Gathering Bot

Bot to help you heard your players.


## Commands

All commands must be prefixed (e.g. `!ping`). 

- `ping`: Ensure the bot is running with a friendly message.
- `rsvp [accept|decline]`: `accept` or `decline` the invitation to the session.
- `vote [dream|cancel]`: Cast your vote for either `dreaming` or `cancelling`
  the session when you do not have a full group of players.


## Config

```ini
[secrets]
token = BOT_TOKEN_HERE

[session]
time =
day =

[discord]
# Channel ID for communication
channelID =
# If you want %, you'll need this as %%
botPrefix =
# User ID (not name) of your Dungeon Master.
# Used for sending them a summary of the upcomming session.
dmID =

[db]
host =
port =
password =
```
