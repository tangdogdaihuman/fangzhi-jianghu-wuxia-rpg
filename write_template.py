
import os
html_content = open(os.path.join(os.path.dirname(__file__), "html_content.txt"), "r", encoding="utf-8").read()
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("Done")
