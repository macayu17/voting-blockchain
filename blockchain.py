import hashlib
import time
import os
from flask import Flask, request, jsonify, render_template_string

# -------------------------
# Blockchain Core Classes
# -------------------------

class Block:
    def __init__(self, index, timestamp, vote_data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.vote_data = vote_data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.vote_data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def proof_of_work(self, difficulty):
        while self.hash[:difficulty] != '0' * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 3
        self.voters = set()  # Track voter IDs to prevent duplicates

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_vote(self, vote_data):
        voter_id = vote_data['voter_id']
        if voter_id in self.voters:
            print(f"[!] Duplicate vote rejected: {voter_id}")
            return False

        prev_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            vote_data=vote_data,
            previous_hash=prev_block.hash
        )
        new_block.proof_of_work(self.difficulty)
        self.chain.append(new_block)
        self.voters.add(voter_id)
        print(f"[+] Vote accepted: {voter_id}")
        return True

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]

            if curr.hash != curr.calculate_hash():
                return False
            if curr.previous_hash != prev.hash:
                return False
        return True

    def tally_votes(self):
        results = {}
        for block in self.chain[1:]:  # Skip genesis block
            vote = block.vote_data['vote']
            results[vote] = results.get(vote, 0) + 1
        return results

# -------------------------
# Flask Web App
# -------------------------

app = Flask(__name__)
voting_chain = Blockchain()

HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <title>Blockchain Voting</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(to right, #e0eafc, #cfdef3);
            font-family: 'Segoe UI', sans-serif;
        }
        .voting-card {
            max-width: 600px;
            margin: auto;
            margin-top: 80px;
            border-radius: 20px;
        }
        .btn-primary {
            background-color: #007bff;
            border: none;
        }
        .btn-outline-success, .btn-outline-secondary {
            width: 48%;
        }
        .header-icon {
            font-size: 2.5rem;
        }
        .form-select, .form-control {
            border-radius: 12px;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="card shadow-lg p-5 bg-white voting-card">
        <div class="text-center mb-4">
            <div class="header-icon mb-2">🗳️</div>
            <h2 class="fw-bold">Blockchain Voting System</h2>
            <p class="text-muted">Your vote is secure, anonymous, and immutable.</p>
        </div>
        <form action="/vote" method="post">
            <div class="mb-3">
                <label for="voter_id" class="form-label">Voter ID</label>
                <input type="text" class="form-control" name="voter_id" placeholder="Enter your voter ID" required>
            </div>
            <div class="mb-3">
                <label for="vote" class="form-label">Select Candidate</label>
                <select class="form-select" name="vote" required>
                    <option value="" disabled selected>Select a candidate</option>
                    <option value="Candidate A">Candidate A</option>
                    <option value="Candidate B">Candidate B</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary w-100 py-2">Submit Vote</button>
        </form>
        <hr class="my-4">
        <div class="d-flex justify-content-between">
            <a href="/results" class="btn btn-outline-success">📊 View Results</a>
            <a href="/chain" class="btn btn-outline-secondary">🔗 View Blockchain</a>
        </div>
    </div>
</div>
</body>
</html>
'''


@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/vote', methods=['POST'])
def vote():
    voter_id = request.form['voter_id']
    vote = request.form['vote']
    success = voting_chain.add_vote({'voter_id': voter_id, 'vote': vote})
    if success:
        return "<h3>✅ Vote submitted successfully!</h3><a href='/'>Back</a>"
    else:
        return "<h3>❌ Duplicate vote detected. Only one vote allowed per voter.</h3><a href='/'>Back</a>"

@app.route('/results')
def results():
    return jsonify(voting_chain.tally_votes())

@app.route('/chain')
def chain():
    return jsonify([
        {
            'index': block.index,
            'timestamp': block.timestamp,
            'vote_data': block.vote_data,
            'hash': block.hash,
            'previous_hash': block.previous_hash
        }
        for block in voting_chain.chain
    ])

# -------------------------
# Run the App (Render Compatible)
# -------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
