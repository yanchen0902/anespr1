from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def serve_flowchart():
    return send_file('flowchart.html')

if __name__ == '__main__':
    app.run(port=8000)
