from flask import Flask, request, jsonify, render_template
from blockchain_dashboard import BlockchainQueryEngine

app = Flask(__name__, template_folder="templates")
engine = BlockchainQueryEngine()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query():
    query_str = request.form.get("query", "")
    if not query_str:
        return jsonify({"error": "No query provided"}), 400

    try:
        results = engine.process_query(query_str)
        return render_template("index.html", query=query_str, results=results)
    except Exception as e:
        return render_template("index.html", error=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
