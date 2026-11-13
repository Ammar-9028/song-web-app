import os, re, requests, subprocess, tempfile
from flask import Flask, render_template, request, send_file, abort, flash, redirect, url_for
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")
ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
DETAILS = "https://archive.org/metadata/{}"

def clean_name(value):
    value = re.sub(r'[^A-Za-z0-9._ -]', '', value or '')
    return value.strip()[:100] or "download"

def search_items(query):
    params = {
        "q": f'({query}) AND mediatype:(movies OR audio)',
        "fl[]": ["identifier", "title", "creator", "mediatype", "year"],
        "rows": 24, "page": 1, "output": "json"
    }
    response = requests.get(ARCHIVE_SEARCH, params=params, timeout=25)
    response.raise_for_status()
    return response.json().get("response", {}).get("docs", [])

@app.route("/", methods=["GET", "POST"])
def index():
    results, query = [], ""
    if request.method == "POST":
        query = request.form.get("q", "").strip()
        if query:
            try:
                results = search_items(query)
            except requests.RequestException:
                flash("Search service abhi respond nahi kar raha. Thodi der baad try karein.")
    return render_template("index.html", results=results, query=query)

@app.route("/download/<identifier>")
def download(identifier):
    # Only download files explicitly marked as public domain or Creative Commons
    # by the Internet Archive metadata record.
    try:
        data = requests.get(DETAILS.format(identifier), timeout=25).json()
        meta = data.get("metadata", {})
        license_text = " ".join(str(meta.get(k, "")) for k in ("licenseurl", "rights", "license"))
        allowed = any(x in license_text.lower() for x in (
            "public domain", "creativecommons.org/publicdomain", "creativecommons.org/licenses"
        ))
        if not allowed:
            abort(403, "Is item ka reuse license verify nahi hua. Sirf authorized/public-domain/CC items download karein.")
        files_meta = data.get("files", [])
        choices = []
        for item in files_meta:
            name = item.get("name", "")
            fmt = item.get("format", "").lower()
            if name.lower().endswith((".mp3", ".mp4", ".m4a", ".ogg", ".wav", ".webm", ".avi", ".mov")):
                choices.append(item)
        if not choices:
            abort(404, "Is item me supported audio/video file nahi mili.")
        # Prefer MP3 for audio records, MP4 for video records.
        media_type = meta.get("mediatype", "")
        preferred = [x for x in choices if (x["name"].lower().endswith(".mp3") if media_type == "audio" else x["name"].lower().endswith(".mp4"))]
        chosen = (preferred or choices)[0]
        url = f"https://archive.org/download/{identifier}/{requests.utils.quote(chosen['name'])}"
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        suffix = pathlib.Path(chosen["name"]).suffix or ".bin"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        for chunk in r.iter_content(1024 * 256):
            if chunk: tmp.write(chunk)
        tmp.close()
        return send_file(tmp.name, as_attachment=True, download_name=clean_name(meta.get("title")) + suffix)
    except requests.RequestException:
        abort(502, "Download source se connection nahi ho paya.")

@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(502)
def errors(error):
    return render_template("error.html", message=getattr(error, "description", "Something went wrong")), error.code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
