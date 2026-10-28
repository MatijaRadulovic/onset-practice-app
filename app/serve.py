"""Tiny server for the onSET practice app.

Run: python3 app/serve.py [port]   ->  http://localhost:8000
Reads ../exam-*/ (text-K-*.md + answers.md) and serves them as JSON.
"""
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent


def parse_answers(path):
    """answers.md -> {text_number: [{kept, missing}, ...]}"""
    result, current = {}, None
    for line in path.read_text().splitlines():
        m = re.match(r"## Text (\d+):", line)
        if m:
            current = int(m.group(1))
            result[current] = []
            continue
        m = re.match(r"\d+\. \*\*(.+?)\*\*(.+?) → ", line)
        if m and current is not None:
            result[current].append({"kept": m.group(1), "missing": m.group(2)})
    return result


def load_exams():
    exams = []
    # original practice test first, then exam-01..10
    for folder in sorted(ROOT.glob("exam-*"), key=lambda p: (p.name != "exam-original", p.name)):
        answers = parse_answers(folder / "answers.md")
        texts = []
        for f in sorted(folder.glob("text-*.md")):
            num = int(re.match(r"text-(\d+)-", f.name).group(1))
            lines = f.read_text().splitlines()
            texts.append(
                {
                    "n": num,
                    "title": lines[0].lstrip("# ").strip(),
                    "body": " ".join(lines[4:]).strip(),  # skip title, blank, italics, blank
                    "answers": answers[num],
                }
            )
        exams.append({"id": folder.name, "texts": sorted(texts, key=lambda t: t["n"])})
    return exams


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/":
            self.send(200, "text/html; charset=utf-8", (APP_DIR / "index.html").read_bytes())
        elif self.path == "/api/exams":
            self.send(200, "application/json", json.dumps(load_exams()).encode())
        else:
            self.send(404, "text/plain", b"not found")

    def send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"onSET practice: http://localhost:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
