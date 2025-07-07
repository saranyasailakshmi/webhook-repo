from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

# Connect to MongoDB (use your connection string if using Atlas)
client = MongoClient("mongodb://localhost:27017/")
db = client["webhookDB"]
collection = db["events"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    payload = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.datetime.utcnow()
    }
    collection.insert_one(payload)
    return jsonify({"message": "Event received"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    events = []
    for doc in collection.find().sort("timestamp", -1).limit(10):
        e = format_event(doc)
        events.append(e)
    return jsonify(events)

def format_event(doc):
    evt = doc['event']
    data = doc['data']
    timestamp = doc['timestamp'].strftime('%d %B %Y - %I:%M %p UTC')

    if evt == "push":
        author = data['pusher']['name']
        branch = data['ref'].split('/')[-1]
        return f'"{author}" pushed to "{branch}" on {timestamp}'
    elif evt == "pull_request":
        author = data['pull_request']['user']['login']
        from_branch = data['pull_request']['head']['ref']
        to_branch = data['pull_request']['base']['ref']
        return f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {timestamp}'
    elif evt == "pull_request" and data['action'] == "closed" and data['pull_request']['merged']:
        author = data['pull_request']['user']['login']
        from_branch = data['pull_request']['head']['ref']
        to_branch = data['pull_request']['base']['ref']
        return f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {timestamp}'
    return "Unknown event"

if __name__ == '__main__':
    app.run(debug=True)
