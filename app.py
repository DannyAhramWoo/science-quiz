#!/usr/bin/env python3
"""과학 경시대회 퀴즈 앱"""

import os
import json
import re
from flask import Flask, jsonify, request, send_from_directory, render_template

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROBLEMS_DIR = os.path.join(BASE_DIR, "problems")
ANSWERS_DIR = os.path.join(BASE_DIR, "answers")
PROGRESS_FILE = os.path.join(BASE_DIR, "progress.json")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def get_category(filename):
    name = os.path.splitext(filename)[0]
    if '_' in name:
        return name.rsplit('_', 1)[0].strip()
    return "기타"


def list_problems():
    categories = {}

    for entry in os.scandir(PROBLEMS_DIR):
        if entry.is_dir():
            cat = entry.name
            for fname in os.listdir(entry.path):
                if os.path.splitext(fname)[1].lower() not in IMAGE_EXTS:
                    continue
                rel_path = f"{cat}/{fname}"
                has_answer = os.path.exists(os.path.join(ANSWERS_DIR, rel_path))
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append({"name": rel_path, "has_answer": has_answer})
        elif entry.is_file():
            if os.path.splitext(entry.name)[1].lower() not in IMAGE_EXTS:
                continue
            cat = get_category(entry.name)
            has_answer = os.path.exists(os.path.join(ANSWERS_DIR, entry.name))
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({"name": entry.name, "has_answer": has_answer})

    for cat in categories:
        categories[cat].sort(key=lambda x: natural_sort_key(x["name"]))

    return dict(sorted(categories.items(), key=lambda x: natural_sort_key(x[0])))


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/images/problems/<path:filename>")
def serve_problem(filename):
    return send_from_directory(PROBLEMS_DIR, filename)


@app.route("/images/answers/<path:filename>")
def serve_answer(filename):
    return send_from_directory(ANSWERS_DIR, filename)


@app.route("/api/problems")
def get_problems():
    return jsonify(list_problems())


@app.route("/api/progress", methods=["GET"])
def get_progress():
    return jsonify(load_progress())


@app.route("/api/progress", methods=["POST"])
def update_progress():
    data = request.json
    name = data["name"]
    correct = data["correct"]

    progress = load_progress()
    if name not in progress:
        progress[name] = {"correct": 0, "wrong": 0, "mastered": False}

    if correct:
        progress[name]["correct"] += 1
        progress[name]["mastered"] = True
    else:
        progress[name]["wrong"] += 1
        progress[name]["correct"] = 0
        progress[name]["mastered"] = False

    save_progress(progress)
    return jsonify({"ok": True, "progress": progress[name]})


@app.route("/api/progress/reset", methods=["POST"])
def reset_progress():
    data = request.json or {}
    if "name" in data:
        progress = load_progress()
        progress.pop(data["name"], None)
        save_progress(progress)
    else:
        save_progress({})
    return jsonify({"ok": True})


if __name__ == "__main__":
    os.makedirs(PROBLEMS_DIR, exist_ok=True)
    os.makedirs(ANSWERS_DIR, exist_ok=True)
    print("=" * 50)
    print("우현서 과학 경시 퀴즈 앱")
    print("브라우저에서 http://localhost:5002 접속")
    print("=" * 50)
    app.run(host="0.0.0.0", debug=False, port=5002)
