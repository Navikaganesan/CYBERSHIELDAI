import csv
import hashlib
import os
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, send_file

from model.predictor import CyberbullyingPredictor
from scraper.instagram_scraper import InstagramScraper

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
except Exception:
    SimpleDocTemplate = None


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

app = Flask(__name__)
predictor = CyberbullyingPredictor()
monitor_lock = threading.Lock()
results_lock = threading.Lock()
analysis_results = []
next_result_id = 1
monitor_state = {
    "active": False,
    "thread": None,
    "reel_url": "",
    "seen": set(),
    "last_error": "",
    "status": "Idle",
    "visible_comments": 0,
    "analyzed_comments": 0,
    "last_comment": "",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def evidence_id(username, comment, reel_url):
    raw = f"{username}|{comment}|{reel_url}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def save_result(username, comment, analysis, reel_url="", profile_url="", timestamp=""):
    global next_result_id
    evidence = evidence_id(username, comment, reel_url)
    timestamp = timestamp or utc_now()
    with results_lock:
        if any(item["evidence_id"] == evidence for item in analysis_results):
            return evidence
        analysis_results.insert(
            0,
            {
                "id": next_result_id,
                "username": username,
                "comment": comment,
                "prediction": analysis["prediction"],
                "confidence": analysis["confidence"],
                "reason": analysis["reason"],
                "timestamp": timestamp,
                "reel_url": reel_url,
                "profile_url": profile_url,
                "evidence_id": evidence,
            },
        )
        next_result_id += 1
    return evidence


def clear_results():
    global next_result_id
    with results_lock:
        analysis_results.clear()
        next_result_id = 1


def fetch_results(limit=200):
    with results_lock:
        return [item.copy() for item in analysis_results[:limit]]


def build_summary(results):
    total = len(results)
    bullying = sum(1 for item in results if item["prediction"] == "Bullying")
    safe = total - bullying
    return {
        "total": total,
        "bullying": bullying,
        "safe": safe,
        "bullying_percentage": round((bullying / total) * 100, 2) if total else 0,
        "monitoring": monitor_state["active"],
        "reel_url": monitor_state["reel_url"],
        "model_status": predictor.model_status,
        "last_error": monitor_state["last_error"],
        "status": monitor_state["status"],
        "visible_comments": monitor_state["visible_comments"],
        "analyzed_comments": monitor_state["analyzed_comments"],
        "last_comment": monitor_state["last_comment"],
    }


def monitor_thread_is_alive():
    thread = monitor_state.get("thread")
    return bool(thread and thread.is_alive())


def monitoring_loop(reel_url):
    scraper = InstagramScraper(headless=False)
    try:
        monitor_state["status"] = "Opening Instagram"
        scraper.open_reel(reel_url)
        monitor_state["status"] = "Scanning comments"
        while monitor_state["active"]:
            comments = scraper.fetch_comments()
            monitor_state["visible_comments"] = len(comments)
            if not comments:
                monitor_state["status"] = "No visible comments found yet"
            for item in comments:
                key = evidence_id(item.username, item.comment, reel_url)
                if key in monitor_state["seen"]:
                    continue
                monitor_state["status"] = f"Analyzing @{item.username}"
                analysis = predictor.predict(item.comment)
                evidence = save_result(
                    item.username,
                    item.comment,
                    analysis,
                    reel_url=reel_url,
                    profile_url=item.profile_url,
                    timestamp=item.timestamp or utc_now(),
                )
                monitor_state["seen"].add(key)
                monitor_state["analyzed_comments"] += 1
                monitor_state["last_comment"] = item.comment[:120]
                monitor_state["status"] = f"Analyzed {monitor_state['analyzed_comments']} comment(s)"
                print(f"Analyzed {evidence}: @{item.username} -> {analysis['prediction']}")
            time.sleep(5)
    except Exception as exc:
        monitor_state["last_error"] = str(exc)
        monitor_state["status"] = f"Stopped: {exc}"
    finally:
        scraper.close()
        monitor_state["active"] = False
        if not monitor_state["last_error"]:
            monitor_state["status"] = "Stopped"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.post("/predict")
def predict_comment():
    payload = request.get_json(force=True)
    comment = payload.get("comment", "").strip()
    if not comment:
        return jsonify({"error": "comment is required"}), 400
    return jsonify(predictor.predict(comment))


@app.get("/start_monitoring")
def start_monitoring():
    reel_url = request.args.get("reel_url", "").strip()
    if not reel_url:
        return jsonify({"error": "reel_url query parameter is required"}), 400
    with monitor_lock:
        if monitor_state["active"] and monitor_thread_is_alive():
            return jsonify({"message": "Monitoring is already running", "status": build_summary(fetch_results())})
        if monitor_state["active"] and not monitor_thread_is_alive():
            monitor_state["active"] = False
            monitor_state["status"] = "Previous monitor stopped"
        monitor_state.update(
            {
                "active": True,
                "reel_url": reel_url,
                "seen": set(),
                "last_error": "",
                "status": "Starting monitor",
                "visible_comments": 0,
                "analyzed_comments": 0,
                "last_comment": "",
            }
        )
        clear_results()
        thread = threading.Thread(target=monitoring_loop, args=(reel_url,), daemon=True)
        monitor_state["thread"] = thread
        thread.start()
    return jsonify({"message": "Monitoring started", "status": build_summary(fetch_results())})


@app.get("/stop_monitoring")
def stop_monitoring():
    monitor_state["active"] = False
    monitor_state["status"] = "Stopping monitor"
    return jsonify({"message": "Monitoring stopped", "status": build_summary(fetch_results())})


@app.get("/results")
def results():
    latest = fetch_results()
    return jsonify({"summary": build_summary(latest), "results": latest})


@app.post("/export_report")
def export_report():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    results = fetch_results(limit=10000)
    if not results:
        return jsonify({"error": "No analyzed comments are available to export yet."}), 400
    report_type = (request.get_json(silent=True) or {}).get("type", "csv").lower()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if report_type == "pdf":
        if SimpleDocTemplate is None:
            return jsonify({"error": "reportlab is not installed. Run pip install -r requirements.txt"}), 500
        path = os.path.join(REPORTS_DIR, f"cybershield_report_{stamp}.pdf")
        table_data = [["Username", "Comment", "Prediction", "Confidence", "Timestamp", "Reel URL"]]
        table_data.extend(
            [
                [
                    item["username"],
                    item["comment"][:80],
                    item["prediction"],
                    f'{item["confidence"]}%',
                    item["timestamp"],
                    item["reel_url"] or "",
                ]
                for item in results
            ]
        )
        document = SimpleDocTemplate(path, pagesize=letter)
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102033")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )
        document.build([table])
        return send_file(path, as_attachment=True)

    path = os.path.join(REPORTS_DIR, f"cybershield_report_{stamp}.csv")
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["username", "comment", "prediction", "confidence", "reason", "timestamp", "reel_url", "profile_url"])
        for item in results:
            writer.writerow(
                [
                    item["username"],
                    item["comment"],
                    item["prediction"],
                    item["confidence"],
                    "; ".join(item["reason"]),
                    item["timestamp"],
                    item["reel_url"],
                    item["profile_url"],
                ]
            )
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
