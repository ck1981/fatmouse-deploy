import os
from flask import Flask
app = Flask(__name__)


@app.route("/")
def hello():
    return "Deploy name: {}".format(os.environ['DEPLOY_NAME'])

if __name__ == "__main__":
    app.run(host='0.0.0.0')
