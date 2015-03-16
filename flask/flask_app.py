import os
import sys
from flask import Flask
app = Flask(__name__)


@app.route("/")
def hello():
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        return "Worker service. Deploy name: {}".format(os.environ['DEPLOY_NAME'])
    else:
        return "Deploy name: {}".format(os.environ['DEPLOY_NAME'])

if __name__ == "__main__":
    app.run(host='0.0.0.0')
