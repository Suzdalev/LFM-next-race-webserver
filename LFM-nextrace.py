import io
import pytz
import requests
from flask import Flask, send_file
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

URL = "https://api3.lowfuelmotorsport.com/api/users/getMySignedUpRaces"

TOKEN = ''
try:
    with open('bearer.txt', 'r') as file:
        TOKEN = file.read()
except:
    print('could not read Bearer TOKEN.\nOpen LFM website in browser, open DevConsole > Network, find "getMySignedUpRaces" request.\nIn the request header you will find bearer token, which you should put into "bearer.txt" near EXE file\n\n\n')
    exit(127)

print("\nResulting image is available on http://127.0.0.1:1715/races\n\n")


HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

def format_timedelta(tdelta):
    """Formats timedelta as 'D days, HH:MM:SS'"""
    days = tdelta.days
    seconds = tdelta.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    txt = f"{days} days, " if days > 0 else ""
    txt += f"{hours:02}:{minutes:02}:{seconds:02}"
    return txt


@app.route("/races")
def races():
    # --- Fetch race data ---
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        race_data = response.json()
    except requests.RequestException as e:
        race_text = f"Error fetching race data:\n{e}"
    else:
        if not race_data:
            race_text = "No upcoming races"
        else:
            tz = pytz.timezone("Etc/GMT-1")
            now = datetime.now(tz)
            lines = []
            for race in race_data:
                race_start_time = datetime.strptime(
                    race["race_date"], "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=tz)
                time_left = race_start_time - now
                line = f"{format_timedelta(time_left)} | #{race['race_id']} | {race['series']} | Split {race['split']}"
                lines.append(line)
            race_text = "\n".join(lines)

    # --- Create image ---
    try:
        font = ImageFont.truetype("impact.ttf", 28)
    except OSError:
        font = ImageFont.load_default()

    lines = race_text.split("\n")

    # Calculate text size accurately
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    text_sizes = []
    max_width = 0
    total_height = 0
    line_spacing = 8  # extra vertical space between lines
    bottom_padding = 6  # prevent clipping descenders

    for line in lines:
        bbox = dummy_draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        text_sizes.append((width, height))
        max_width = max(max_width, width)
        total_height += height + line_spacing

    total_height += bottom_padding
    margin = 2
    img_width = max_width + margin * 2
    img_height = total_height + margin * 2

    img = Image.new("RGB", (img_width, img_height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    y = margin
    for line, (w, h) in zip(lines, text_sizes):
        draw.text((margin, y), line, font=font, fill=(255, 255, 255))
        y += h + line_spacing

    # --- Return image as PNG ---
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1715)