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
        self.candidates = ["Candidate A", "Candidate B"]  # Default candidates list

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

    def add_candidate(self, candidate_name):
        """Add a new candidate to the list"""
        if candidate_name not in self.candidates:
            self.candidates.append(candidate_name)
            print(f"[+] Candidate added: {candidate_name}")
            return True
        print(f"[!] Candidate already exists: {candidate_name}")
        return False

    def modify_candidate(self, old_name, new_name):
        """Modify the name of an existing candidate"""
        if old_name in self.candidates:
            index = self.candidates.index(old_name)
            self.candidates[index] = new_name
            print(f"[+] Candidate name updated from {old_name} to {new_name}")
            return True
        print(f"[!] Candidate not found: {old_name}")
        return False

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
        .results-table th, .results-table td {
            text-align: center;
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
                    {% for candidate in candidates %}
                    <option value="{{ candidate }}">{{ candidate }}</option>
                    {% endfor %}
                </select>
            </div>
            <button type="submit" class="btn btn-primary w-100 py-2">Submit Vote</button>
        </form>
        <hr class="my-4">
        <div class="d-flex justify-content-between">
            <a href="/results" class="btn btn-outline-success">📊 View Results</a>
            <a href="/chain" class="btn btn-outline-secondary">🔗 View Blockchain</a>
            <a href="/candidates" class="btn btn-outline-secondary">📝 Manage Candidates</a>
        </div>
    </div>
</div>
</body>
</html>
'''

# -------------------------
# Routes
# -------------------------

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, candidates=voting_chain.candidates)

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
    results = voting_chain.tally_votes()
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Vote Results</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container">
        <div class="card shadow-lg p-5 bg-white voting-card">
            <div class="text-center mb-4">
                <h2 class="fw-bold">Election Results</h2>
                <p class="text-muted">Current vote tally</p>
            </div>
            <table class="table table-bordered results-table">
                <thead>
                    <tr>
                        <th>Candidate</th>
                        <th>Votes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for candidate, votes in results.items() %}
                    <tr>
                        <td>{{ candidate }}</td>
                        <td>{{ votes }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="/" class="btn btn-primary w-100 py-2">Back to Voting</a>
        </div>
    </div>
    </body>
    </html>
    ''', results=results)

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

@app.route('/candidates', methods=['GET', 'POST'])
def manage_candidates():
    if request.method == 'POST':
        action = request.form.get('action')
        candidate_name = request.form.get('candidate_name')

        if action == 'add':
            voting_chain.add_candidate(candidate_name)
        elif action == 'modify':
            old_name = request.form.get('old_name')
            voting_chain.modify_candidate(old_name, candidate_name)

    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Manage Candidates</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container">
        <div class="card shadow-lg p-5 bg-white voting-card">
            <div class="text-center mb-4">
                <h2 class="fw-bold">Manage Candidates</h2>
                <p class="text-muted">Add or modify candidates for the election.</p>
            </div>
            <h4>Current Candidates</h4>
            <ul>
                {% for candidate in candidates %}
                    <li>{{ candidate }}</li>
                {% endfor %}
            </ul>
            <form action="/candidates" method="post">
                <div class="mb-3">
                    <label for="candidate_name" class="form-label">Candidate Name</label>
                    <input type="text" class="form-control" name="candidate_name" required>
                </div>
                <div class="mb-3">
                    <label for="action" class="form-label">Action</label>
                    <select class="form-select" name="action" required>
                        <option value="add">Add Candidate</option>
                        <option value="modify">Modify Candidate</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label for="old_name" class="form-label">Old Name (for Modify action)</label>
                    <input type="text" class="form-control" name="old_name">
                </div>
                <button type="submit" class="btn btn-primary w-100 py-2">Submit</button>
            </form>
        </div>
    </div>
    </body>
    </html>
    ''', candidates=voting_chain.candidates)

# -------------------------
# Run the App (Render Compatible)
# -------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
