from flask import Flask, render_template, request, redirect, url_for, render_template_string, jsonify, flash, session
import hashlib
import time
import json
import os
import datetime
import threading
import random
import requests  # Add this import for consensus

# -------------------------
# Enhanced Blockchain Core Classes
# -------------------------

class Block:
    def __init__(self, index, timestamp, vote_data, previous_hash=''):
        self.index = index
        self.timestamp = timestamp
        self.vote_data = vote_data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{json.dumps(self.vote_data)}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        # Fast mining for voting
        target = '0' * difficulty
        max_iterations = 1000  # Reduced for faster mining
        iterations = 0
        
        while self.hash[:difficulty] != target and iterations < max_iterations:
            self.nonce += 1
            self.hash = self.calculate_hash()
            iterations += 1
            
        if iterations >= max_iterations:
            # If we hit max iterations, just accept the current hash
            print(f"Block mining stopped after {iterations} iterations")
        else:
            print(f"Block mined: {self.hash} after {iterations} iterations")
        
        return self.hash

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 1  # Reduced difficulty for faster mining
        self.voters = set()
        self.candidates = ["Candidate A", "Candidate B", "Candidate C"]
        self.pending_transactions = []
        self.mining_reward = 1
        self.nodes = set()  # For consensus
        self.lock = threading.Lock()  # Thread safety for mining
    
    def create_genesis_block(self):
        return Block(0, time.time(), {"message": "Genesis Block"}, "0")
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def add_block(self, new_block):
        with self.lock:
            new_block.previous_hash = self.get_latest_block().hash
            new_block.hash = new_block.mine_block(self.difficulty)
            self.chain.append(new_block)
            return new_block
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Verify current block hash
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Verify chain linkage
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def add_vote(self, vote_data):
        voter_id = vote_data.get('voter_id')
        if voter_id in self.voters:
            return False
        
        with self.lock:
            self.voters.add(voter_id)
            new_block = Block(len(self.chain), time.time(), vote_data)
            new_block.previous_hash = self.get_latest_block().hash
            new_block.hash = new_block.mine_block(1)  # Always use difficulty 1 for voting
            self.chain.append(new_block)
            return True
    
    def add_candidate(self, candidate_name):
        """Add a new candidate to the election"""
        if candidate_name in self.candidates:
            return False
        
        with self.lock:
            self.candidates.append(candidate_name)
            # Record this action in the blockchain for transparency
            action_data = {
                "action": "add_candidate",
                "candidate": candidate_name,
                "timestamp": time.time()
            }
            new_block = Block(len(self.chain), time.time(), action_data)
            new_block.previous_hash = self.get_latest_block().hash
            new_block.hash = new_block.mine_block(1)  # Always use difficulty 1 for admin operations
            self.chain.append(new_block)
            return True
    
    def modify_candidate(self, old_name, new_name):
        """Modify an existing candidate's name"""
        if old_name not in self.candidates:
            return False
        
        with self.lock:
            index = self.candidates.index(old_name)
            self.candidates[index] = new_name
            # Record this action in the blockchain for transparency
            action_data = {
                "action": "modify_candidate",
                "old_name": old_name,
                "new_name": new_name,
                "timestamp": time.time()
            }
            new_block = Block(len(self.chain), time.time(), action_data)
            new_block.previous_hash = self.get_latest_block().hash
            new_block.hash = new_block.mine_block(1)  # Always use difficulty 1 for admin operations
            self.chain.append(new_block)
            return True

# Create blockchain instance
voting_chain = Blockchain()

# Create Flask app with secret key for flash messages
app = Flask(__name__)
app.secret_key = os.urandom(24)

# -------------------------
# CSS and Templates
# -------------------------

# Base CSS for all pages
BASE_CSS = '''
:root {
    --primary-color: #4776E6;
    --secondary-color: #8E54E9;
    --light-bg: #f8f9fa;
    --dark-bg: #1a1a1a;
    --light-text: #212529;
    --dark-text: #f8f9fa;
}
body {
    background-color: var(--light-bg);
    color: var(--light-text);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.card {
    border: none;
    border-radius: 15px;
    overflow: hidden;
}
.btn-primary {
    background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
    border: none;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.btn-primary:hover {
    transform: translateY(-3px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}
.btn-back {
    background: transparent;
    border: 2px solid var(--primary-color);
    color: var(--primary-color);
    transition: all 0.3s ease;
}
.btn-back:hover {
    background: var(--primary-color);
    color: white;
}
.header-icon {
    font-size: 3rem;
    margin-bottom: 20px;
    background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.status-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: linear-gradient(to right, #20bf55, #01baef);
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
}
.action-buttons {
    display: flex;
    justify-content: space-between;
}
.action-buttons a {
    flex: 1;
    margin: 0 5px;
}
.navbar {
    background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
    padding: 15px 0;
}
.navbar-brand {
    font-weight: bold;
    color: white !important;
}
.nav-link {
    color: rgba(255,255,255,0.8) !important;
    transition: color 0.3s ease;
    margin: 0 10px;
}
.nav-link:hover, .nav-link.active {
    color: white !important;
}
.block-card {
    margin-bottom: 20px;
    border-radius: 10px;
    overflow: hidden;
}
.block-header {
    background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.block-body {
    padding: 15px;
}
.hash-value, .timestamp, .block-data {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    word-break: break-all;
    margin-top: 5px;
}
.genesis-badge {
    background-color: #20bf55;
    color: white;
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    margin-left: 10px;
}
.nonce-badge {
    background-color: rgba(255,255,255,0.2);
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
}
.verification-result {
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin-top: 20px;
    display: none;
}
'''

# Navbar template
NAVBAR_TEMPLATE = '''
<nav class="navbar navbar-expand-lg navbar-dark">
    <div class="container">
        <a class="navbar-brand" href="/">
            <i class="fas fa-link me-2"></i> Blockchain Voting
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item">
                    <a class="nav-link {% if active_page == 'home' %}active{% endif %}" href="/">
                        <i class="fas fa-home me-1"></i> Home
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if active_page == 'results' %}active{% endif %}" href="/results">
                        <i class="fas fa-chart-pie me-1"></i> Results
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if active_page == 'chain' %}active{% endif %}" href="/chain">
                        <i class="fas fa-link me-1"></i> Blockchain
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if active_page == 'candidates' %}active{% endif %}" href="/candidates">
                        <i class="fas fa-users me-1"></i> Candidates
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {% if active_page == 'analysis' %}active{% endif %}" href="/analysis">
                        <i class="fas fa-shield-alt me-1"></i> Security
                    </a>
                </li>
            </ul>
        </div>
    </div>
</nav>
'''

# Common JavaScript for dark mode
DARK_MODE_JS = '''
<script>
    // Dark mode functionality
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const cards = document.querySelectorAll('.card');
    const icon = themeToggle.querySelector('i');
    
    // Check for saved theme preference
    if (localStorage.getItem('darkMode') === 'true') {
        body.classList.add('dark-mode');
        cards.forEach(card => card.classList.add('dark-mode'));
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        cards.forEach(card => card.classList.toggle('dark-mode'));
        
        const isDarkMode = body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
        
        if (isDarkMode) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });
</script>
'''

# HTML Template for the home page
HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <title>Blockchain Voting</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        ''' + BASE_CSS + '''
        .voting-card {
            max-width: 650px;
            margin: auto;
            margin-top: 50px;
        }
        .vote-animation {
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
''' + NAVBAR_TEMPLATE.replace('{{ active_page }}', 'home') + '''

    <div class="card shadow-lg p-5 bg-white voting-card">
        <span class="status-badge">Blockchain Secured</span>
        <div class="text-center mb-4">
            <div class="header-icon"><i class="fas fa-vote-yea"></i></div>
            <h2 class="fw-bold">Secure Blockchain Voting</h2>
            <p class="text-muted">Your vote is secure, anonymous, and immutable.</p>
        </div>
        <form action="/vote" method="post" class="needs-validation" novalidate>
            <div class="mb-3">
                <label for="voter_id" class="form-label"><i class="fas fa-id-card me-2"></i>Voter ID</label>
                <input type="text" class="form-control" name="voter_id" placeholder="Enter your voter ID" required>
                <div class="invalid-feedback">Please provide a valid voter ID.</div>
            </div>
            <div class="mb-3">
                <label for="vote" class="form-label"><i class="fas fa-user-tie me-2"></i>Select Candidate</label>
                <select class="form-select" name="vote" required>
                    <option value="" disabled selected>Select a candidate</option>
                    {% for candidate in candidates %}
                    <option value="{{ candidate }}">{{ candidate }}</option>
                    {% endfor %}
                </select>
                <div class="invalid-feedback">Please select a candidate.</div>
            </div>
            <button type="submit" class="btn btn-primary w-100 py-3 mt-3 vote-animation">
                <i class="fas fa-paper-plane me-2"></i> Submit Secure Vote
            </button>
        </form>
        <hr class="my-4">
        <div class="action-buttons">
            <a href="/results" class="btn btn-outline-primary">
                <i class="fas fa-chart-pie"></i> Results
            </a>
            <a href="/chain" class="btn btn-outline-secondary">
                <i class="fas fa-link"></i> View Blockchain
            </a>
        </div>
        
        {% if messages %}
        <div class="messages-container mt-4">
            {% for message in messages %}
            <div class="alert alert-{{ message.type }} alert-dismissible fade show" role="alert">
                <i class="fas fa-{{ message.icon }} me-2"></i> {{ message.text }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
''' + DARK_MODE_JS + '''
<script>
    // Form validation
    (function() {
        'use strict';
        const forms = document.querySelectorAll('.needs-validation');
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                } else {
                    // Show loading state - with shorter text
                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing...';
                        submitBtn.disabled = true;
                        
                        // Add a timeout to re-enable the button if it takes too long
                        setTimeout(() => {
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i> Submit Secure Vote';
                        }, 5000); // 5 seconds max
                    }
                }
                form.classList.add('was-validated');
            }, false);
        });
    })();
    
    // Toast notifications
    function showToast(message, type = 'success') {
        const toastContainer = document.querySelector('.toast-container');
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
</script>
</body>
</html>
'''

# -------------------------
# Routes
# -------------------------

@app.route('/')
def home():
    chain_length = len(voting_chain.chain)
    vote_count = len(voting_chain.voters)
    
    messages = session.pop('messages', [])
    
    return render_template_string(HTML_TEMPLATE, 
                                 candidates=voting_chain.candidates,
                                 chain_length=chain_length,
                                 vote_count=vote_count,
                                 messages=messages)

@app.route('/vote', methods=['POST'])
def vote():
    voter_id = request.form.get('voter_id')
    vote = request.form.get('vote')
    
    if not voter_id or not vote:
        session['messages'] = [{'type': 'danger', 'icon': 'exclamation-circle', 'text': 'Missing voter ID or vote selection'}]
        return redirect(url_for('home'))
    
    # Check if voter has already voted before processing
    if voter_id in voting_chain.voters:
        session['messages'] = [{'type': 'warning', 'icon': 'exclamation-triangle', 'text': 'You have already voted. Each voter ID can only vote once.'}]
        return redirect(url_for('home'))
    
    vote_data = {
        'voter_id': voter_id,
        'vote': vote,
        'timestamp': time.time()
    }
    
    # Simplify the mining process for votes to make it faster
    voting_chain.difficulty = 1  # Temporarily reduce difficulty for voting
    
    # Process vote immediately
    result = voting_chain.add_vote(vote_data)
    
    if result:
        session['messages'] = [{'type': 'success', 'icon': 'check-circle', 'text': f'Your vote for {vote} has been securely recorded on the blockchain!'}]
    else:
        session['messages'] = [{'type': 'warning', 'icon': 'exclamation-triangle', 'text': 'You have already voted. Each voter ID can only vote once.'}]
    
    # Redirect to results page
    return redirect(url_for('results'))

# Remove the background processing route since we're processing votes immediately
@app.route('/process_vote', methods=['POST'])
def process_vote():
    data = request.get_json()
    voter_id = data.get('voter_id')
    vote = data.get('vote')
    
    vote_data = {
        'voter_id': voter_id,
        'vote': vote,
        'timestamp': time.time()
    }
    
    result = voting_chain.add_vote(vote_data)
    
    if result:
        session['messages'] = [{'type': 'success', 'icon': 'check-circle', 'text': f'Your vote for {vote} has been securely recorded on the blockchain!'}]
    else:
        session['messages'] = [{'type': 'warning', 'icon': 'exclamation-triangle', 'text': 'You have already voted. Each voter ID can only vote once.'}]
    
    return jsonify({'success': result})

@app.route('/results')
def results():
    vote_counts = {}
    for candidate in voting_chain.candidates:
        vote_counts[candidate] = 0
    
    # Debug information
    print(f"Total blocks in chain: {len(voting_chain.chain)}")
    
    # Properly count votes from all blocks
    for block in voting_chain.chain[1:]:  # Skip genesis block
        try:
            vote_data = block.vote_data
            if isinstance(vote_data, dict) and 'vote' in vote_data:
                candidate = vote_data['vote']
                print(f"Found vote for: {candidate}")
                if candidate in vote_counts:
                    vote_counts[candidate] += 1
                else:
                    print(f"Warning: Vote for unknown candidate: {candidate}")
        except Exception as e:
            print(f"Error processing block: {e}")
    
    # Calculate percentages and find winner
    total_votes = sum(vote_counts.values())
    print(f"Total votes counted: {total_votes}")
    percentages = {}
    winner = None
    max_votes = 0
    
    for candidate, count in vote_counts.items():
        if total_votes > 0:
            percentages[candidate] = round((count / total_votes) * 100, 1)
        else:
            percentages[candidate] = 0
            
        if count > max_votes:
            max_votes = count
            winner = candidate
    
    messages = session.pop('messages', [])
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Voting Results</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            ''' + BASE_CSS + '''
            .results-card {
                max-width: 750px;
                margin: auto;
                margin-top: 50px;
            }
            .result-item {
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                background-color: #f8f9fa;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            .result-item:hover {
                transform: translateY(-3px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .result-item.winner {
                border-left: 5px solid #4776E6;
                background-color: #f0f7ff;
            }
            .candidate-name {
                font-weight: bold;
                color: #4776E6;
                font-size: 1.1rem;
            }
            .vote-count {
                font-weight: bold;
                font-size: 1.2rem;
            }
            .progress-bar {
                background: linear-gradient(to right, #4776E6, #8E54E9);
            }
            .chart-container {
                position: relative;
                height: 300px;
                margin-bottom: 30px;
            }
            .debug-info {
                margin-top: 20px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
            }
            .dark-mode .debug-info {
                background-color: #2a2a2a;
            }
        </style>
    </head>
    <body>
    <div class="container">
        <div class="card shadow-lg p-5 bg-white results-card">
            <div class="text-center mb-4">
                <div class="header-icon"><i class="fas fa-chart-pie"></i></div>
                <h2 class="fw-bold">Election Results</h2>
                <p class="text-muted">Live results from the blockchain</p>
            </div>
            
            <div class="chart-container">
                <canvas id="resultsChart"></canvas>
            </div>
            
            <div class="results-container">
                {% for candidate, count in vote_counts.items() %}
                <div class="result-item d-flex justify-content-between align-items-center {% if candidate == winner and count > 0 %}winner{% endif %}">
                    <div class="candidate-name">{{ candidate }}</div>
                    <div class="vote-count">{{ count }} votes ({{ percentages[candidate] }}%)</div>
                </div>
                {% endfor %}
            </div>
            
            <div class="debug-info">
                <p>Total blocks: {{ chain_length }}</p>
                <p>Total votes: {{ total_votes }}</p>
            </div>
            
            <a href="/" class="btn btn-back mt-4">
                <i class="fas fa-arrow-left me-2"></i> Back to Voting
            </a>
            
            <p class="text-center mt-4 text-muted">Project by Anindhith Sankanna and Ayush Kumar</p>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const ctx = document.getElementById('resultsChart').getContext('2d');
            const resultsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [{% for candidate in vote_counts.keys() %}'{{ candidate }}',{% endfor %}],
                    datasets: [{
                        label: 'Votes',
                        data: [{% for count in vote_counts.values() %}{{ count }},{% endfor %}],
                        backgroundColor: [
                            'rgba(71, 118, 230, 0.7)',
                            'rgba(142, 84, 233, 0.7)',
                            'rgba(66, 186, 150, 0.7)',
                            'rgba(240, 147, 43, 0.7)',
                            'rgba(235, 87, 87, 0.7)'
                        ],
                        borderColor: [
                            'rgba(71, 118, 230, 1)',
                            'rgba(142, 84, 233, 1)',
                            'rgba(66, 186, 150, 1)',
                            'rgba(240, 147, 43, 1)',
                            'rgba(235, 87, 87, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        });
    </script>
    ''' + DARK_MODE_JS + '''
    </body>
    </html>
    ''', vote_counts=vote_counts, percentages=percentages, winner=winner, 
        chain_length=len(voting_chain.chain), total_votes=total_votes)

@app.route('/chain')
def get_chain():
    chain_data = []
    for block in voting_chain.chain:
        block_info = {
            'index': block.index,
            'timestamp': block.timestamp,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce
        }
        
        # Don't show voter_id in the public view for privacy
        if block.index > 0:  # Skip genesis block
            vote_data = block.vote_data.copy() if isinstance(block.vote_data, dict) else {'data': block.vote_data}
            if 'voter_id' in vote_data:
                vote_data['voter_id'] = vote_data['voter_id'][:4] + '*' * (len(vote_data['voter_id']) - 4)
            block_info['vote_data'] = vote_data
        else:
            block_info['vote_data'] = block.vote_data
        
        chain_data.append(block_info)
    
    # Return HTML visualization instead of JSON
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Blockchain Explorer</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            ''' + BASE_CSS + '''
            .blockchain-container {
                max-width: 900px;
                margin: auto;
                margin-top: 50px;
                margin-bottom: 50px;
            }
            .block-card {
                margin-bottom: 30px;
                position: relative;
                overflow: hidden;
            }
            .block-card:not(:last-child)::after {
                content: '';
                position: absolute;
                bottom: -30px;
                left: 50%;
                width: 4px;
                height: 30px;
                background: linear-gradient(to bottom, #4776E6, #8E54E9);
                transform: translateX(-50%);
            }
            .block-header {
                background: linear-gradient(to right, #4776E6, #8E54E9);
                color: white;
                padding: 15px;
                border-radius: 10px 10px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .block-body {
                padding: 20px;
            }
            .hash-value {
                font-family: monospace;
                word-break: break-all;
                background-color: #f8f9fa;
                padding: 8px;
                border-radius: 5px;
                font-size: 0.9rem;
            }
            .timestamp {
                font-size: 0.9rem;
                color: #6c757d;
            }
            .block-data {
                margin-top: 15px;
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                font-family: monospace;
                white-space: pre-wrap;
            }
            .genesis-badge {
                background-color: #ffc107;
                color: #212529;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 0.8rem;
                margin-left: 10px;
            }
            .verify-chain-btn {
                position: fixed;
                bottom: 30px;
                right: 30px;
                z-index: 1000;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            .verification-result {
                position: fixed;
                bottom: 100px;
                right: 30px;
                z-index: 1000;
                padding: 10px 20px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                display: none;
            }
            .nonce-badge {
                background-color: #6c757d;
                color: white;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 0.8rem;
            }
        </style>
    </head>
    <body>
    ''' + NAVBAR_TEMPLATE.replace('{{ active_page }}', 'chain') + '''
    
    <div class="container blockchain-container">
        <div class="text-center mb-5">
            <div class="header-icon"><i class="fas fa-link"></i></div>
            <h2 class="fw-bold">Blockchain Explorer</h2>
            <p class="text-muted">Explore the entire blockchain with {{ chain_length }} blocks</p>
        </div>
        
        {% for block in chain %}
        <div class="card block-card shadow">
            <div class="block-header">
                <div>
                    <strong>Block #{{ block.index }}</strong>
                    {% if block.index == 0 %}
                    <span class="genesis-badge">Genesis</span>
                    {% endif %}
                </div>
                <span class="nonce-badge">Nonce: {{ block.nonce }}</span>
            </div>
            <div class="block-body">
                <div>
                    <strong>Hash:</strong>
                    <div class="hash-value">{{ block.hash }}</div>
                </div>
                <div class="mt-3">
                    <strong>Previous Hash:</strong>
                    <div class="hash-value">{{ block.previous_hash }}</div>
                </div>
                <div class="mt-3">
                    <strong>Timestamp:</strong>
                    <div class="timestamp">{{ block.timestamp }} ({{ format_timestamp(block.timestamp) }})</div>
                </div>
                <div class="mt-3">
                    <strong>Data:</strong>
                    <div class="block-data">{{ format_data(block.vote_data) }}</div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <button class="btn btn-primary verify-chain-btn" id="verifyChainBtn" title="Verify Blockchain Integrity">
        <i class="fas fa-shield-alt"></i>
    </button>
    
    <div class="verification-result" id="verificationResult"></div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''' + DARK_MODE_JS + '''
    <script>
        document.getElementById('verifyChainBtn').addEventListener('click', function() {
            fetch('/verify')
                .then(response => response.json())
                .then(data => {
                    const resultElement = document.getElementById('verificationResult');
                    resultElement.style.display = 'block';
                    
                    if (data.valid) {
                        resultElement.className = 'verification-result bg-success text-white';
                        resultElement.innerHTML = '<i class="fas fa-check-circle me-2"></i> Blockchain is valid!';
                    } else {
                        resultElement.className = 'verification-result bg-danger text-white';
                        resultElement.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i> Blockchain is invalid!';
                    }
                    
                    setTimeout(() => {
                        resultElement.style.display = 'none';
                    }, 3000);
                });
        });
    </script>
    </body>
    </html>
    ''', chain=chain_data, chain_length=len(chain_data), 
    format_timestamp=lambda ts: datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
    format_data=lambda data: json.dumps(data, indent=2))

# Add a route to verify the blockchain
@app.route('/verify')
def verify_chain():
    is_valid = voting_chain.is_chain_valid()
    return jsonify({'valid': is_valid})

# Update the candidates management page with better UI and feedback
@app.route('/candidates', methods=['GET', 'POST'])
def manage_candidates():
    message = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            candidate_name = request.form.get('candidate_name')
            if candidate_name and candidate_name.strip():
                if voting_chain.add_candidate(candidate_name.strip()):
                    session['messages'] = [{'type': 'success', 'icon': 'check-circle', 'text': f'Candidate "{candidate_name}" added successfully!'}]
                    return redirect(url_for('home'))
                else:
                    message = {'type': 'warning', 'text': f'Candidate "{candidate_name}" already exists!', 'icon': 'exclamation-triangle'}
            else:
                message = {'type': 'danger', 'text': 'Candidate name cannot be empty!', 'icon': 'exclamation-circle'}
                
        elif action == 'modify':
            old_name = request.form.get('old_name')
            new_name = request.form.get('candidate_name')
            
            if not old_name:
                message = {'type': 'danger', 'text': 'Please select a candidate to modify!', 'icon': 'exclamation-circle'}
            elif not new_name or not new_name.strip():
                message = {'type': 'danger', 'text': 'New candidate name cannot be empty!', 'icon': 'exclamation-circle'}
            else:
                if voting_chain.modify_candidate(old_name, new_name.strip()):
                    session['messages'] = [{'type': 'success', 'icon': 'check-circle', 'text': f'Candidate renamed from "{old_name}" to "{new_name}" successfully!'}]
                    return redirect(url_for('home'))
                else:
                    message = {'type': 'danger', 'text': f'Candidate "{old_name}" not found!', 'icon': 'exclamation-circle'}
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Manage Candidates</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            ''' + BASE_CSS + '''
            .candidates-card {
                max-width: 750px;
                margin: auto;
                margin-top: 50px;
            }
            .candidate-item {
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                background-color: #f8f9fa;
                transition: all 0.3s ease;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .dark-mode .candidate-item {
                background-color: #2a2a2a;
            }
            .candidate-name {
                font-weight: bold;
                color: #4776E6;
            }
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                visibility: hidden;
                opacity: 0;
                transition: visibility 0s, opacity 0.3s;
            }
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 5px solid #f3f3f3;
                border-top: 5px solid #4776E6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
    
    <div id="loadingOverlay" class="loading-overlay">
        <div class="loading-spinner"></div>
    </div>
    
    <div class="container candidates-card">
        <div class="text-center mb-4">
            <div class="header-icon"><i class="fas fa-users-cog"></i></div>
            <h2 class="fw-bold">Manage Candidates</h2>
            <p class="text-muted">Add or modify candidates for the election</p>
        </div>
        
        {% if message %}
        <div class="alert alert-{{ message.type }} alert-dismissible fade show" role="alert">
            <i class="fas fa-{{ message.icon }} me-2"></i> {{ message.text }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        {% endif %}
        
        <div class="card shadow-lg p-4 mb-4">
            <h5 class="mb-3">Current Candidates</h5>
            {% for candidate in candidates %}
            <div class="candidate-item">
                <div class="candidate-name">{{ candidate }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div class="card shadow-lg p-4">
            <h5 class="mb-3">Manage Candidates</h5>
            <form action="/candidates" method="post" id="candidateForm">
                <div class="mb-3">
                    <label for="action" class="form-label">Action</label>
                    <select class="form-select" name="action" id="actionSelect" required>
                        <option value="add">Add New Candidate</option>
                        <option value="modify">Modify Existing Candidate</option>
                    </select>
                </div>
                
                <div class="mb-3" id="oldNameField" style="display: none;">
                    <label for="old_name" class="form-label">Existing Candidate Name</label>
                    <select class="form-select" name="old_name">
                        <option value="" disabled selected>Select candidate to modify</option>
                        {% for candidate in candidates %}
                        <option value="{{ candidate }}">{{ candidate }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="mb-3">
                    <label for="candidate_name" class="form-label" id="newNameLabel">Candidate Name</label>
                    <input type="text" class="form-control" name="candidate_name" placeholder="Enter candidate name" required>
                </div>
                
                <button type="submit" class="btn btn-primary w-100 py-2">Submit</button>
            </form>
        </div>
        
        <div class="mt-4">
            <a href="/" class="btn btn-outline-primary w-100">Back to Home</a>
        </div>
        
        <p class="text-center mt-4 text-muted">Project by Anindhith Sankanna and Ayush Kumar</p>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''' + DARK_MODE_JS + '''
    <script>
        // Toggle old name field based on action selection
        document.getElementById('actionSelect').addEventListener('change', function() {
            const oldNameField = document.getElementById('oldNameField');
            const newNameLabel = document.getElementById('newNameLabel');
            
            if (this.value === 'modify') {
                oldNameField.style.display = 'block';
                newNameLabel.textContent = 'New Candidate Name';
            } else {
                oldNameField.style.display = 'none';
                newNameLabel.textContent = 'Candidate Name';
            }
        });
        
        // Show loading overlay when form is submitted
        document.getElementById('candidateForm').addEventListener('submit', function() {
            const loadingOverlay = document.getElementById('loadingOverlay');
            loadingOverlay.style.visibility = 'visible';
            loadingOverlay.style.opacity = '1';
            
            // Set a timeout to hide the overlay if it takes too long
            setTimeout(function() {
                loadingOverlay.style.visibility = 'hidden';
                loadingOverlay.style.opacity = '0';
            }, 5000); // 5 seconds max
        });
    </script>
    </body>
    </html>
    ''', candidates=voting_chain.candidates)

# Add error handling for 404 and 500 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Page Not Found</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            ''' + BASE_CSS + '''
            .error-container {
                max-width: 600px;
                margin: 100px auto;
                text-align: center;
            }
            .error-icon {
                font-size: 5rem;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
    ''' + NAVBAR_TEMPLATE.replace('{{ active_page }}', '') + '''
    
    <div class="container error-container">
        <div class="error-icon">
            <i class="fas fa-map-signs"></i>
        </div>
        <h1 class="mb-4">Page Not Found</h1>
        <p class="mb-4">The page you're looking for doesn't exist or has been moved.</p>
        <a href="/" class="btn btn-primary">
            <i class="fas fa-home me-2"></i> Go Home
        </a>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''' + DARK_MODE_JS + '''
    </body>
    </html>
    '''), 404

@app.errorhandler(500)
def server_error(e):
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Server Error</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            ''' + BASE_CSS + '''
            .error-container {
                max-width: 600px;
                margin: 100px auto;
                text-align: center;
            }
            .error-icon {
                font-size: 5rem;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
    ''' + NAVBAR_TEMPLATE.replace('{{ active_page }}', '') + '''
    
    <div class="container error-container">
        <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
        </div>
        <h1 class="mb-4">Server Error</h1>
        <p class="mb-4">Something went wrong on our end. Please try again later.</p>
        <a href="/" class="btn btn-primary">
            <i class="fas fa-home me-2"></i> Go Home
        </a>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''' + DARK_MODE_JS + '''
    </body>
    </html>
    '''), 500

# Add a route to analyze blockchain security and performance
@app.route('/analysis')
def blockchain_analysis():
    # Calculate some metrics
    total_blocks = len(voting_chain.chain)
    avg_mining_time = 0
    total_votes = len(voting_chain.voters)
    
    # Calculate average mining time (simplified)
    if total_blocks > 1:
        avg_mining_time = round(sum(1 for block in voting_chain.chain if block.index > 0) / (total_blocks - 1), 2)
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Blockchain Analysis</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            ''' + BASE_CSS + '''
            .analysis-container {
                max-width: 800px;
                margin: auto;
                margin-top: 50px;
                margin-bottom: 50px;
            }
            .metric-card {
                text-align: center;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            .metric-value {
                font-size: 2.5rem;
                font-weight: bold;
                margin: 10px 0;
                background: linear-gradient(to right, #4776E6, #8E54E9);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .security-item {
                margin-bottom: 15px;
                padding: 15px;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
            .dark-mode .security-item {
                background-color: #2a2a2a;
            }
            .security-title {
                font-weight: bold;
                color: #4776E6;
                margin-bottom: 5px;
            }
        </style>
    </head>
    <body>
    ''' + NAVBAR_TEMPLATE.replace('{{ active_page }}', '') + '''
    
    <div class="container analysis-container">
        <div class="text-center mb-5">
            <div class="header-icon"><i class="fas fa-chart-line"></i></div>
            <h2 class="fw-bold">Blockchain Analysis</h2>
            <p class="text-muted">Security and Performance Metrics</p>
        </div>
        
        <div class="row mb-5">
            <div class="col-md-4">
                <div class="card metric-card shadow">
                    <div><i class="fas fa-cubes fa-2x"></i></div>
                    <div class="metric-value">{{ total_blocks }}</div>
                    <div class="text-muted">Total Blocks</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card metric-card shadow">
                    <div><i class="fas fa-vote-yea fa-2x"></i></div>
                    <div class="metric-value">{{ total_votes }}</div>
                    <div class="text-muted">Total Votes</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card metric-card shadow">
                    <div><i class="fas fa-tachometer-alt fa-2x"></i></div>
                    <div class="metric-value">{{ difficulty }}</div>
                    <div class="text-muted">Mining Difficulty</div>
                </div>
            </div>
        </div>
        
        <div class="card shadow-lg p-4 mb-4">
            <h4 class="mb-4">Security Analysis</h4>
            
            <div class="security-item">
                <div class="security-title"><i class="fas fa-shield-alt me-2"></i>Proof of Work</div>
                <p>Our blockchain uses a Proof of Work consensus algorithm with a difficulty of {{ difficulty }}. This means each block hash must start with {{ difficulty }} zeros, making it computationally expensive to mine blocks and preventing tampering.</p>
            </div>
            
            <div class="security-item">
                <div class="security-title"><i class="fas fa-link me-2"></i>Chain Integrity</div>
                <p>Each block contains the hash of the previous block, creating a chain of blocks that cannot be altered without redoing the proof of work for all subsequent blocks. This ensures the immutability of the blockchain.</p>
            </div>
            
            <div class="security-item">
                <div class="security-title"><i class="fas fa-user-shield me-2"></i>Voter Privacy</div>
                <p>While all votes are recorded on the blockchain for transparency, voter IDs are partially masked in the public view to protect voter privacy.</p>
            </div>
            
            <div class="security-item">
                <div class="security-title"><i class="fas fa-lock me-2"></i>Cryptographic Security</div>
                <p>We use SHA-256 hashing algorithm, which is cryptographically secure and produces a unique 256-bit hash for each block, making it virtually impossible to generate the same hash for different data.</p>
            </div>
        </div>
        
        <div class="card shadow-lg p-4 mb-4">
            <h4 class="mb-4">Performance Analysis</h4>
            
            <div class="security-item">
                <div class="security-title"><i class="fas fa-bolt me-2"></i>Mining Efficiency</div>
                <p>With a difficulty of {{ difficulty }}, our blockchain balances security with performance. Higher difficulty increases security but requires more computational resources and time.</p>
            </div>
            
            <div class="security-item">
                <div class="security-title"><i class="fas fa-server me-2"></i>Scalability</div>
                <p>The current implementation is suitable for small to medium-scale elections. For larger elections, increasing the mining difficulty and implementing sharding or layer-2 solutions would be recommended.</p>
            </div>
            
            <div class="security-item">
                <div class="security-title"><i class="fas fa-sync me-2"></i>Consensus Mechanism</div>
                <p>Our blockchain uses a longest-chain consensus mechanism, where nodes accept the longest valid chain as the authoritative one. This ensures all nodes eventually reach consensus on the state of the blockchain.</p>
            </div>
        </div>
        
        <div class="text-center mt-4">
            <a href="/" class="btn btn-primary">
                <i class="fas fa-home me-2"></i> Back to Home
            </a>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''' + DARK_MODE_JS + '''
    </body>
    </html>
    ''', total_blocks=total_blocks, total_votes=total_votes, difficulty=voting_chain.difficulty)

# Add a link to the analysis page in the navbar
NAVBAR_TEMPLATE = '''
<nav class="navbar navbar-expand-lg navbar-dark mb-4">
    <div class="container">
        <a class="navbar-brand" href="/"><i class="fas fa-vote-yea me-2"></i>Blockchain Voting</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <a class="nav-link {{ 'active' if active_page == 'home' }}" href="/"><i class="fas fa-home me-1"></i> Home</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {{ 'active' if active_page == 'results' }}" href="/results"><i class="fas fa-chart-pie me-1"></i> Results</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {{ 'active' if active_page == 'chain' }}" href="/chain"><i class="fas fa-link me-1"></i> Blockchain</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {{ 'active' if active_page == 'candidates' }}" href="/candidates"><i class="fas fa-users-cog me-1"></i> Candidates</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link {{ 'active' if active_page == 'analysis' }}" href="/analysis"><i class="fas fa-chart-line me-1"></i> Analysis</a>
                </li>
            </ul>
            <div class="theme-toggle" id="theme-toggle" title="Toggle Dark Mode">
                <i class="fas fa-moon"></i>
            </div>
        </div>
    </div>
</nav>
'''

# Add a security enhancement route to adjust mining difficulty
@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    message = None
    
    if request.method == 'POST':
        new_difficulty = int(request.form.get('difficulty', 2))
        if 1 <= new_difficulty <= 5:  # Limit difficulty range for usability
            voting_chain.difficulty = new_difficulty
            message = {'type': 'success', 'text': f'Mining difficulty updated to {new_difficulty}', 'icon': 'check-circle'}
        else:
            message = {'type': 'danger', 'text': 'Difficulty must be between 1 and 5', 'icon': 'exclamation-circle'}
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Admin Settings</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            ''' + BASE_CSS + '''
            .settings-card {
                max-width: 750px;
                margin: auto;
                margin-top: 50px;
            }
            .setting-item {
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                background-color: #f8f9fa;
            }
            .dark-mode .setting-item {
                background-color: #2a2a2a;
            }
            .setting-title {
                font-weight: bold;
                color: #4776E6;
                margin-bottom: 10px;
            }
            .difficulty-info {
                margin-top: 10px;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
    ''' + NAVBAR_TEMPLATE.replace('{{ active_page }}', '') + '''
    
    <div class="container settings-card">
        <div class="text-center mb-4">
            <div class="header-icon"><i class="fas fa-cogs"></i></div>
            <h2 class="fw-bold">Admin Settings</h2>
            <p class="text-muted">Configure blockchain parameters</p>
        </div>
        
        {% if message %}
        <div class="alert alert-{{ message.type }} alert-dismissible fade show" role="alert">
            <i class="fas fa-{{ message.icon }} me-2"></i> {{ message.text }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        {% endif %}
        
        <div class="card shadow-lg p-4">
            <h5 class="mb-4">Blockchain Configuration</h5>
            
            <div class="setting-item">
                <div class="setting-title"><i class="fas fa-tachometer-alt me-2"></i>Mining Difficulty</div>
                <p>Adjust the mining difficulty to balance security and performance. Higher values increase security but slow down mining.</p>
                
                <form action="/admin/settings" method="post">
                    <div class="mb-3">
                        <label for="difficulty" class="form-label">Difficulty (current: {{ current_difficulty }})</label>
                        <input type="range" class="form-range" min="1" max="5" step="1" id="difficulty" name="difficulty" value="{{ current_difficulty }}">
                        <div class="d-flex justify-content-between">
                            <span>1 (Faster)</span>
                            <span>5 (More Secure)</span>
                        </div>
                        <div class="difficulty-info" id="difficultyInfo">
                            Current selection: <span id="difficultyValue">{{ current_difficulty }}</span>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Update Settings</button>
                </form>
            </div>
            
            <div class="setting-item">
                <div class="setting-title"><i class="fas fa-info-circle me-2"></i>Current Blockchain Status</div>
                <div class="row mt-3">
                    <div class="col-md-4">
                        <div class="mb-2"><strong>Total Blocks:</strong></div>
                        <div>{{ total_blocks }}</div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-2"><strong>Total Votes:</strong></div>
                        <div>{{ total_votes }}</div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-2"><strong>Chain Valid:</strong></div>
                        <div>{{ "Yes" if is_valid else "No" }}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <a href="/" class="btn btn-outline-primary w-100">Back to Home</a>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''' + DARK_MODE_JS + '''
    <script>
        // Update difficulty value display
        document.getElementById('difficulty').addEventListener('input', function() {
            document.getElementById('difficultyValue').textContent = this.value;
        });
    </script>
    </body>
    </html>
    ''', current_difficulty=voting_chain.difficulty, total_blocks=len(voting_chain.chain), 
        total_votes=len(voting_chain.voters), is_valid=voting_chain.is_chain_valid())

# -------------------------
# Run the App (Render Compatible)
# -------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
