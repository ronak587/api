from flask import Flask, request, jsonify
import requests
import base64
import time
import json
import hmac
import hashlib
import urllib.parse

app = Flask(__name__)

SECRET = "S7O1qf3ZRyNLYA"

def generate_jwt():
    exp = int(time.time()) + 600
    token = {"exp": exp}

    header = base64.urlsafe_b64encode(json.dumps({'typ': 'JWT', 'alg': 'HS256'}).encode()).decode().strip("=")
    payload = base64.urlsafe_b64encode(json.dumps(token).encode()).decode().strip("=")

    signature = hmac.new(SECRET.encode(), f'{header}.{payload}'.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(signature).decode().strip("=")

    jwt = f"{header}.{payload}.{signature}"
    return jwt

def http(url, headers, method="GET", data=None, return_headers=False):
    response = requests.request(method, url, headers=headers, json=data if data else None)
    if response.status_code != 200:
        return None
    return response.json() if not return_headers else response.headers

def download_video(video_url):
    video_id = video_url.split("/")[-1]
    api_url = "https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    
    data = {
        "videoId": video_id,
        "context": {
            "client": {
                "hl": "en",
                "clientName": "WEB",
                "clientVersion": "2.20231219.04.00"
            }
        },
        "playbackContext": {
            "contentPlaybackContext": {
                "signatureTimestamp": "19709",
                "referer": video_url
            }
        }
    }
    
    headers = {
        "Host": "www.youtube.com",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "okhttp/4.11.0"
    }
    
    response = http(api_url, headers, method="POST", data=data)
    print(response)
    if not response or "streamingData" not in response:
        return jsonify({"message": "Failed to retrieve video formats."}), 400

    videos = []
    for format_data in response["streamingData"]["formats"]:
        video = {
            "url": urllib.parse.unquote(format_data["url"]),
            "quality": format_data.get("qualityLabel", "Unknown"),
            "title": response["videoDetails"]["title"]
        }
        videos.append(video)
    
    return videos

@app.route('/')
def index():
    source = request.args.get("source")
    vUrl = request.args.get("url")
    
    if not vUrl or not source:
        return jsonify({"message": "Video Url/Source not found..."})

    jwt = generate_jwt()
    url = f'https://api.snapx.info/v1/{source}?url={urllib.parse.quote(vUrl)}'

    headers = {
        'X-App-Id': '22120300515132',
        'X-App-Token': jwt,
        'Accept': 'application/json',
        'Accept-Charset': 'UTF-8',
        'User-Agent': 'Ktor client',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': 'api.snapx.info',
        'Connection': 'Keep-Alive'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({"message": "Something Went Wrong..."})

    json_response = response.json()

    if source == "instagram":
        message = json_response.get('message')
        videoUrl = json_response.get('data', {}).get('video_url')
        output = {"message": message, "videoUrl": videoUrl}
        return jsonify(output)

    if source == "fb":
        message = json_response.get('message')
        hd = json_response.get('data', {}).get('hd')
        sd = json_response.get('data', {}).get('sd')
        output = {"message": message, "hd": hd, "sd": sd}
        return jsonify(output)

    if source == "twitter":
        videos = []
        for format_data in json_response["data"]["playlists"]:
            video = {
                "quality": format_data["resolution"],
                "url": urllib.parse.unquote(format_data["playlist_url"])
            }
            videos.append(video)
        return jsonify(videos)

    if source == "youtube":
        return jsonify(download_video(vUrl))

    return jsonify({"message": "Source not recognized."})

if __name__ == "__main__":
    app.run(debug=True)
