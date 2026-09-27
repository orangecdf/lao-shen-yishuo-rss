#!/bin/sh
set -eu
cd /root/lao-shen-yishuo-rss
/usr/bin/python3 generate_feed.py
git add feed.xml
if ! git diff --cached --quiet; then
  git config user.name "lao-shen-rss-bot"
  git config user.email "lao-shen-rss-bot@users.noreply.github.com"
  git commit -m "Refresh RSS feed"
  git push origin main
fi
