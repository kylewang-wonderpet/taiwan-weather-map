#!/usr/bin/env bash
# Install CJK fonts for Chinese character rendering
apt-get install -y fonts-noto-cjk 2>/dev/null || true
fc-cache -fv 2>/dev/null || true
# Install Python dependencies
pip install -r requirements.txt
