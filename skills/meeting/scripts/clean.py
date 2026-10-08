#!/usr/bin/env python3
"""Strip inline base64 images from a meeting transcript and print the cleaned text.

Usage: clean.py <transcript.md> > cleaned.md
"""
import re
import sys

text = open(sys.argv[1]).read()
text = re.sub(r"!\[[^\]]*\]\(data:image/[a-z]+;base64,[A-Za-z0-9+/=]+\)", "[image]", text)
text = re.sub(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", "[image]", text)
text = re.sub(r"^\[image\]:.*$", "", text, flags=re.M)
sys.stdout.write(text)
