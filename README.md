# not-so-anonymous-bot
A feature-full telegram bot to administer an anonymous channel. 

First install the requirements with the following command:

```bash
pip3 install -r requirement.txt
```

Then set the following configurations in a file named `.env`:

# Configurations
| Variable            | Description                                                                     |
| ------------------- | ------------------------------------------------------------------------------- |
| APP_ENVIRONMENT     | The envorinment that bot runs in. Can be either 'developement' or 'production'. |
| APP_MAINTENANCE     | Indicates whether the bot is in the maintenance mode. can be either 0 or 1.     |
| TELEGRAM_API_ID     | Telegram api id for the bot.                                                    |
| TELEGRAM_API_HASH   | Telegram api hash for the bot.                                                  |
| TELEGRAM_BOT_TOKEN  | Telegram bot token for the bot.                                                 |
| CHANNEL_ID          | Id of the anonymous channel.                                                    |
| CHANNEL_ADMIN       | Admin's id of the anonymous channel.                                            |
| BOT_ID              | Id of the bot.                                                                  |
| MYSQL_DB            | MySQL database name.                                                            |
| MYSQL_HOST          | Host name of the MySQL database.                                                |
| MYSQL_PORT          | Port number of the MySQL database.                                              |
| MYSQL_USER          | Username of the MySQL database.                                                 |
| MYSQL_PASSWORD      | Password of the MySQL database.                                                 |
| MYSQL_POOL_SIZE     | Pool size of the MySQL database.                                                |

You also need to configure loggers. First make a file named `config` in the main directory, and create two files named `logger.dev.conf` and `logger.prod.conf`. These two configuration files are used in `developement` and `production` environments, respectively. Looger configuration format follows the python logger module configuration style. Other optional configurations are also put into `config` directory.

Then you can start the bot server:

```bash
python3 src/launcher.py
```

Enjoy!