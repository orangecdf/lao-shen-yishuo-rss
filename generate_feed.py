#!/usr/bin/env python3
import datetime as dt
import hashlib
import hmac
import html
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import format_datetime

CHANNEL_ID = "100798"
API = "https://i.qingting.fm/capi"


def get_json(url):
    req = urllib.request.Request(url, headers={"Referer": "https://www.qingting.fm/", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def media_url(program_id):
    path = f"/audiostream/redirect/{CHANNEL_ID}/{program_id}?access_token=&device_id=MOBILESITE&qingting_id=&t={int(dt.datetime.now().timestamp() * 1000)}"
    sign = hmac.new(b"fpMn12&38f_2e", path.encode(), hashlib.md5).hexdigest()
    return "https://audio.qingting.fm" + path + "&sign=" + sign


def text(parent, tag, value, **attrs):
    e = ET.SubElement(parent, tag, attrs)
    e.text = str(value)
    return e


def main():
    channel = get_json(f"{API}/v3/channel/{CHANNEL_ID}")["data"]
    version = channel["v"]
    all_programs = []
    for page in (1, 2):
        url = f"{API}/channel/{CHANNEL_ID}/programs/{version}?curpage={page}&pagesize=100&order=asc"
        all_programs.extend(get_json(url)["data"]["programs"])
    # Keep every episode, even if the upstream later changes its total.
    seen = set()
    programs = [p for p in all_programs if not (p["id"] in seen or seen.add(p["id"]))]

    rss = ET.Element("rss", {"version": "2.0", "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"})
    ch = ET.SubElement(rss, "channel")
    text(ch, "title", channel["title"])
    text(ch, "link", f"https://www.qingting.fm/channels/{CHANNEL_ID}")
    text(ch, "description", channel.get("description", "知识类节目《老沈一说》"))
    text(ch, "language", "zh-CN")
    text(ch, "generator", "lao-shen-yishuo-rss")
    image = channel.get("thumbs", {}).get("400_thumb", "")
    if image:
        im = ET.SubElement(ch, "image")
        text(im, "url", image)
        text(im, "title", channel["title"])
        text(im, "link", f"https://www.qingting.fm/channels/{CHANNEL_ID}")
    text(ch, "itunes:author", "沈永鹏")
    text(ch, "itunes:explicit", "false")

    for p in programs:
        item = ET.SubElement(ch, "item")
        title = p.get("title", "")
        link = f"https://www.qingting.fm/channels/{CHANNEL_ID}/programs/{p['id']}/"
        text(item, "title", title)
        text(item, "link", link)
        text(item, "guid", link, isPermaLink="true")
        try:
            when = dt.datetime.strptime(p["update_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
            pub = format_datetime(when)
        except Exception:
            pub = p.get("update_time", "")
        text(item, "pubDate", pub)
        text(item, "description", html.escape(title))
        enc = ET.SubElement(item, "enclosure", {"url": media_url(p["id"]), "type": "audio/x-m4a", "length": str((p.get("file_size") or [0])[-1])})
        text(item, "itunes:duration", p.get("duration", 0))
        if p.get("cover"):
            text(item, "itunes:image", "", href=p["cover"])

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"generated {len(programs)} episodes")


if __name__ == "__main__":
    main()
