
from flask import Flask, request, render_template
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os

app = Flask(__name__)

advanced_checklist = [
    {"label": "Mentions légales détectées", "score": 10, "keyword": "mentions légales"},
    {"label": "Politique de confidentialité présente", "score": 10, "keyword": "politique de confidentialité"},
    {"label": "Formulaire de contact détecté", "score": 10, "tag": "form"},
    {"label": "Consentement cookie détecté (Google, etc.)", "score": 10, "script_keywords": ["gtag", "googletagmanager", "analytics"]},
    {"label": "Conditions générales identifiées", "score": 5, "keyword": "conditions générales"},
    {"label": "Présence de lien vers les réseaux sociaux", "score": 5, "keywords": ["facebook.com", "linkedin.com", "twitter.com"]},
    {"label": "HTTPS activé", "score": 5, "https": True}
]

def scan_advanced(url):
    try:
        response = requests.get(url, timeout=10)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        all_text = soup.get_text(separator=' ', strip=True).lower()
        results = []

        for item in advanced_checklist:
            found = False
            if "keyword" in item and item["keyword"] in all_text:
                found = True
            elif "keywords" in item:
                found = any(k in all_text for k in item["keywords"])
            elif "tag" in item:
                found = bool(soup.find_all(item["tag"]))
            elif "script_keywords" in item:
                scripts = soup.find_all("script")
                found = any(any(k in (s.get_text() or "") for k in item["script_keywords"]) for s in scripts)
            elif "https" in item and url.startswith("https"):
                found = True

            results.append({
                "Critère": item["label"],
                "Score attribué": item["score"] if found else 0,
                "Présence détectée": "Oui" if found else "Non"
            })

        return pd.DataFrame(results)
    except Exception as e:
        return pd.DataFrame([{"Critère": "Erreur de chargement", "Score attribué": 0, "Présence détectée": str(e)}])

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    url = ""
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            df = scan_advanced(url)
            results = df.to_dict(orient="records")
    return render_template("index.html", results=results, url=url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
