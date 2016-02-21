from flask import Flask
from flask import render_template, request, redirect, url_for
app = Flask(__name__)

from argparse import ArgumentParser

import utils
import pickle
import os
import atexit
import signal
import sys

class LeaderboardRecord(object):
    def __init__(self):
        self.scores = {}

    def update_score(self, problem, score):
        self.scores[problem] = max(self.scores.get(problem, 0), score)

    def get_score(self, problem):
        return self.scores.get(problem, 0)

class Leaderboard(object):
    def __init__(self):
        self.records = {}

    def update_record(self, name, problem, score):
        if not name in self.records:
            self.records[name] = LeaderboardRecord()
        self.records[name].update_score(problem, score)

    def get_sorted_records(self):
        # TODO: Sort them!
        return self.records

    def save(self, path):
        open(path, "w").write(pickle.dumps(self.records))

    def load(self, path):
        if os.path.exists(path):
            self.records = pickle.loads(open(path, "r").read())

leaderboard = Leaderboard()
leaderboard_path = None

def grade_submission(name, problem, submission):
    data = utils.read_data("data/" + problem)

    taken = map(int, submission.split(' '))

    total_profit = 0
    total_weight = 0
    for item in taken:
        if item < 1 or item > len(data["weights"]):
            return "Incorrect item %s" % item

        total_weight += data["weights"][item - 1]
        total_profit += data["profits"][item - 1]

    if total_weight > data["capacity"]:
        return "Weight overflow: {} > {}".format(total_weight, data["capacity"])

    leaderboard.update_record(name, problem, total_profit)
    leaderboard.save(leaderboard_page)

    return "Total profit: %s" % total_profit

@app.route("/")
def main_page():
    return "Hello World!"

@app.route("/submit", methods=["GET", "POST"])
def submit_page():
    if request.method == "POST":
        submission = request.files["file"]
        name = request.form["name"]
        problem = request.form["problem"]
        verdict = grade_submission(name, problem, submission.read())
        return redirect(url_for("leaderboard_page", verdict=verdict))
    return render_template("submit.html")

@app.route("/leaderboard")
def leaderboard_page():
    items = leaderboard.get_sorted_records()
    problems = ["1", "2"]
    verdict = request.args.get("verdict")
    return render_template(
            "leaderboard.html",
            items=items,
            problems=problems,
            verdict=verdict)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run web server")

    parser.add_argument(
        "--leaderboard",
        type=str,
        default="leaderboard",
        help="Path to leaderboard file")

    args = parser.parse_args()

    leaderboard_path = args.leaderboard
    leaderboard.load(args.leaderboard)
    app.debug = True
    app.run(host="0.0.0.0", port=args.port)

