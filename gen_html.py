#!/usr/bin/env python3
import os
html = []
html.append("<!DOCTYPE html>")
html.append("<html>\<head>")
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(chr(10).join(html))
print("done")
