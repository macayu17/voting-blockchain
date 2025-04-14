# Blockchain Voting System

This is a **Blockchain-based Voting System** that ensures secure, anonymous, and immutable voting using blockchain technology. It provides a decentralized and transparent way to conduct elections, where the votes are stored in blocks that are cryptographically secured, preventing any tampering or unauthorized modification.

## Features
- **Blockchain Security**: Each vote is recorded in a blockchain, making it tamper-proof and transparent.
- **Prevent Duplicate Votes**: Voter ID is tracked to ensure each voter can only vote once.
- **Vote Tallying**: Results are automatically tallied in real-time and displayed to users.
- **Dark Mode Toggle**: Users can switch between light and dark modes for a better user experience.
- **Manage Candidates**: Admin can add or modify candidate names.
- **CSV Export**: Export voting results in CSV format for further analysis or record-keeping.
- **Web Interface**: A user-friendly web interface built with **Flask** and **Bootstrap** for easy access to the voting system.

## Technologies Used
- **Python**: The core programming language used for building the blockchain and web application.
- **Flask**: A micro web framework for building the web application.
- **Bootstrap**: A front-end framework for creating responsive UI components.
- **Hashlib**: Used for generating SHA-256 hashes for securing the blockchain.
- **CSV**: For exporting voting results.

## Requirements
- Python 3.x
- Flask
- Any modern browser (Google Chrome, Firefox, etc.)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/blockchain-voting-system.git
   cd blockchain-voting-system
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
3. Run the application:

    ```bash
    python app.py
    ```
By default, the app will run on http://127.0.0.1:5000.
