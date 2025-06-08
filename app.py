from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World from Python! This is to lear AWS deployment via GH Actions"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

