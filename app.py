from flask import Flask
from src.BotBlocker.botblocker import BotBlocker

app = Flask(__name__)

bot_blocker = BotBlocker(app, rules = {("path", "contains", "/"): {"action": "allow"}})

@app.route("/")
def index():
    return "Hello, World!"


if __name__ == "__main__":
    app.run()
