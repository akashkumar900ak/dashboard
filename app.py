from flask import Flask, request, jsonify
from blockchain_dashboard import BlockchainQueryEngine

app = Flask(__name__)
engine = BlockchainQueryEngine()

@app.route("/")
def home():
    return "🧠 Smart Blockchain Query API is live! Use /query"

@app.route("/query", methods=["POST"])
def query():
    data = request.json
    query_str = data.get("query", "")
    if not query_str:
        return jsonify({"error": "No query provided"}), 400

    try:
        results = engine.process_query(query_str)
        wallets = [wallet.__dict__ for wallet in results]
        return jsonify({"query": query_str, "results": wallets})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
