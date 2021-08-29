# Discord D&D Gathering Bot

Bot to help you heard your players.


## Commands

All commands must be prefixed (e.g. `!ping`). The prefix is determined by the [server-side config](#config).

- `ping`: Ensure the bot is running with a friendly message.
- `uptime`: How long the bot has been running.
- `config`: Walks the DM through configuring the bot.
- `commands`: Lists all available commands.
- `reset`: Resets the RSVP and voting lists.
- `rsvp [accept|decline]`: `accept` or `decline` the invitation to the session.
- `vote [dream|cancel]`: Cast your vote for either `dreaming` or `cancelling`
  the session when you do not have a full group of players.
- `skip`: "Skips" the current week; disables alerting.
- `list`: Displays the RSVP and voting lists.
- `inv [add|remove|update]`: Alone, `inv` will dispay the caller's inventory. Paired with `add`, `remove`, or `update` will add, remove, or update quantities of items respectively.
  - `inv add QTY:ITEM_NAME, QTY:ITEM_NAME, [...]`: Add multiple items in quantity:name pairs.
  - `inv remove ITEM_NAME`: Removes item `ITEM_NAME` from inventory. Note, this does not _use_ (decrement quantity) an item, but removes it completely.
  - `inv update QTY:ITEM_NAME, QTY:ITEM_NAME, [...]`: Update the quantities of multiple items.


## Config

Server-side configuration is done via a config file. Copy `config-template.ini` to `config.ini` and fill in the details.

```ini
[secrets]
token = BOT_TOKEN_HERE

[discord]

# If you want %, you'll need this as %%
botPrefix =

[db]
# MongoDB connection details
host =
port =
password =
```

> Note: This can all be done with environment variables instead. In the absence of a config file, the bot will fall 
> back to using environment variables.


## Discord Config

After inviting the bot, the DM should use the `config` command in the "meeting hall" channel (i.e. the channel you wish 
to receive alerts and keep track of players).

- session day: Day of the session.
- session time: Time of the session in 24h, HH:MM format.
- first alert: First _alert_ from the bot reminding players to RSVP.
- second alert: Second RSVP reminder.
