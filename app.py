import os
import time
from flask import Flask, render_template, request, redirect, url_for
from model.detector import analyze_text
from database.db import insert_history, get_all_history, delete_by_ids, delete_by_time, init_db

app = Flask(__name__)

# Initialize DB
init_db()


# Home Page
@app.route("/", methods=["GET", "POST"])
def home():
    prefill_text = request.args.get("text", "")

    if request.method == "POST":
        user_text = request.form["text"]

        if not user_text.strip():
            return render_template("index.html", result=None, error="Please enter a message")

        time.sleep(1.5)
        result = analyze_text(user_text)

        insert_history(user_text, result["score"], result["risk"])

        return render_template("index.html", result=result)

    return render_template("index.html", result=None, prefill_text=prefill_text)


# Result Page (Re-analyze)
@app.route("/result")
def result_page():
    text = request.args.get("text")
    result = analyze_text(text)

    return render_template("index.html", result=result)


# History Page
@app.route("/history")
def show_history():
    history = get_all_history()
    return render_template("history.html", history=history)


# Delete Selected
@app.route("/delete-selected", methods=["POST"])
def delete_selected():
    selected = request.form.getlist("selected")

    if selected:
        delete_by_ids(selected)

    return redirect("/history")


# Delete by Time Range
@app.route("/delete-range/<int:hours>")
def delete_range(hours):
    delete_by_time(hours)
    return redirect("/history")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)