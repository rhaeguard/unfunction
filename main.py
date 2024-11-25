import markdown
import pathlib
import os
import glob
import shutil
from datetime import datetime
import sass
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

CODE_EXTRACTION_REGEX = (
    r"<pre><code class=\"language-([a-z]+)\">((.|\n)+?)<\/code><\/pre>"
)

build_path = pathlib.Path("./build")

with open("./templates/html_template.html") as html_file:
    HTML_TEMPLATE = html_file.read().strip()

with open("./templates/single_post.html") as html_file:
    SINGLE_POST_TEMPLATE = html_file.read().strip()

if not build_path.exists():
    os.makedirs(build_path, exist_ok=True)

posts_metadata = []

PYGMENTS_HTML_FORMATTER = HtmlFormatter(style="monokai")


def hilite_code(match):
    lang = match.group(1)
    code = match.group(2)

    code = code.replace("&amp;", "&")
    code = code.replace("&lt;", "<")
    code = code.replace("&gt;", ">")
    code = code.replace("&quot;", '"')

    lexer = get_lexer_by_name(lang, stripall=True)
    return highlight(code, lexer, PYGMENTS_HTML_FORMATTER)


with open("./main.scss") as scss_file, open("./build/main.css", "w+") as main_css:
    raw_scss = scss_file.read().strip()

    syntax_highligher_styling = PYGMENTS_HTML_FORMATTER.get_style_defs()

    syntax_highligher_styling = f"""
    .highlight {{
        {syntax_highligher_styling}
    }}
    """

    raw_scss += syntax_highligher_styling

    compiled_css = sass.compile(string=raw_scss, output_style="compressed")

    main_css.write(compiled_css)
    main_css.flush()

# build the files
for markdown_file in glob.glob("./content/posts/*.md"):
    filename = pathlib.Path(markdown_file).name[:-3]
    with open(markdown_file, encoding="utf-8") as f, open(
        f"./build/{filename}.html", "w+", encoding="utf-8"
    ) as o:
        out_html = markdown.markdown(
            f.read(),
            extensions=["fenced_code", "sane_lists"],
        )

        out_html = re.sub(CODE_EXTRACTION_REGEX, hilite_code, out_html, 0, re.MULTILINE)

        metadata_end_ix = out_html.find("-->")
        post_metadata = {"filename": f"{filename}.html"}
        if metadata_end_ix != -1:
            metadata = out_html[4:metadata_end_ix]
            for meta in metadata.splitlines():
                if not meta.strip():
                    continue

                key, value = meta.strip().split("=", maxsplit=1)
                key, value = key.strip(), value.strip()
                post_metadata[key] = value

            posts_metadata.append(post_metadata)

            out_html = out_html[metadata_end_ix + 3 :]
        out_html = SINGLE_POST_TEMPLATE.replace("{{CONTENT}}", out_html).replace(
            "{{TITLE}}", post_metadata.get("title", ""), 2
        )
        out_html = HTML_TEMPLATE.replace("{{CONTENT}}", out_html).replace(
            "{{TITLE}}", post_metadata.get("title", ""), 2
        )

        o.write(out_html)
        o.flush()

# move the static assets
for file in glob.glob("./static/*"):
    filename = pathlib.Path(file).name
    shutil.copy2(file, f"./build/{filename}")


def build_posts(all_posts):
    output = "<ul>"
    for post in all_posts:
        filename = post["filename"]
        title = post["title"]
        date = post["date"]
        date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z").date()
        is_draft = post["draft"]
        output += f'<li><span>{date}</span>&nbsp;<a href="{filename}">{title}</a></li>'
    output += "</ul>"
    return output


def build_projects(projects):
    output = "<ul>"
    for project in projects:
        t = project["title"]
        u = project["url"]
        output += f'<li><a href="{u}">{t}</a></li>'
    output += "</ul>"

    return output


ALL_PROJECTS = [
    {
        "title": "visualizations with canvas api",
        "url": "https://rhaeguard.github.io/visualizations/",
    },
    {
        "title": "phont - rendering ttf fonts from scratch",
        "url": "https://github.com/rhaeguard/phont",
    },
    {
        "title": "rgx - a tiny regex engine",
        "url": "https://github.com/rhaeguard/rgx",
    },
    {
        "title": "shum - a concatenative language for jvm",
        "url": "https://github.com/rhaeguard/shum",
    },
    {
        "title": "snake - a snake game with procedurally-generated maps",
        "url": "https://github.com/rhaeguard/snake",
    },
    {
        "title": "cells - a spreadsheet with lisp-like formulas",
        "url": "https://github.com/rhaeguard/cells",
    },
]

# construct index.html
with open("./templates/index.html") as html_file, open(
    "./build/index.html", "w+", encoding="utf-8"
) as o:
    index_html = html_file.read().strip()
    posts = build_posts(posts_metadata)
    projects = build_projects(ALL_PROJECTS)
    index_html = index_html.replace("{{POSTS}}", posts).replace(
        "{{PROJECTS}}", projects
    )
    out_html = HTML_TEMPLATE.replace("{{CONTENT}}", index_html).replace(
        "{{TITLE}}", "rhaeguard's blog"
    )
    o.write(out_html)
    o.flush()
