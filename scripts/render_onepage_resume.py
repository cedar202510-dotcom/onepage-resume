#!/usr/bin/env python3
"""
Render a one-page resume HTML from normalized JSON input.

Usage:
  python3 scripts/render_onepage_resume.py \
    --input resume.json \
    --output resume.html \
    --style stripe \
    --accent '#1f4e8c' \
    --sidebar-bg '#1f1f1f'
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path


STYLE_ALIASES = {
    "classic": "stripe",
    "modern": "sidebar",
    "minimal": "compact",
}

STYLE_DEFAULTS = {
    "stripe": {
        "text_primary": "#151515",
        "text_secondary": "#444444",
        "rule": "#d5d5d5",
        "accent": "#1f4e8c",
        "bg": "#ffffff",
        "font": '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
    },
    "compact": {
        "text_primary": "#101010",
        "text_secondary": "#3a3a3a",
        "rule": "#bcbcbc",
        "accent": "#111111",
        "bg": "#ffffff",
        "font": '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
    },
    "sidebar": {
        "text_primary": "#151515",
        "text_secondary": "#4b4b4b",
        "rule": "#d2d2d2",
        "accent": "#111111",
        "bg": "#ffffff",
        "sidebar_bg": "#1f1f1f",
        "font": '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
    },
}

HEX_PATTERN = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def esc(value: str) -> str:
    return html.escape(value or "")


def normalize_hex(value: str, fallback: str) -> str:
    if not value:
        return fallback
    v = value.strip()
    if not HEX_PATTERN.match(v):
        return fallback
    if len(v) == 4:
        return "#" + "".join(ch * 2 for ch in v[1:])
    return v.lower()


def text_color_for_bg(hex_color: str) -> str:
    hex_color = normalize_hex(hex_color, "#000000")
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return "#ffffff" if luminance < 150 else "#111111"


def sanitize_filename_part(value: str, fallback: str) -> str:
    text = (value or "").strip()
    if not text:
        text = fallback
    text = re.sub(r'[\\/:*?"<>|]+', "", text)
    text = re.sub(r"\s+", "-", text)
    text = text.strip("-._")
    return text or fallback


def default_output_path(input_path: str, style: str, data: dict) -> Path:
    profile = data.get("profile", {}) if isinstance(data, dict) else {}
    name = sanitize_filename_part(profile.get("name", ""), "个人简历")
    style_name = sanitize_filename_part(style, "stripe")
    date_tag = datetime.now().strftime("%Y%m%d")
    filename = f"{name}-个人简历-{style_name}-{date_tag}.html"
    return Path(input_path).resolve().parent / filename


def join_non_empty(parts: list[str], sep: str = " | ") -> str:
    return sep.join([p for p in parts if p])


def render_list(items: list[str], marker: str = "disc") -> str:
    if not items:
        return ""
    li = "\n".join(f"<li>{esc(item)}</li>" for item in items if item)
    if not li:
        return ""
    return f'<ul class="marker-{marker}">{li}</ul>'


def render_entry_title(left: str, right: str) -> str:
    return (
        '<div class="entry-title">'
        f'<div class="left">{esc(left)}</div>'
        f'<div class="right">{esc(right)}</div>'
        "</div>"
    )


def section_block(title: str, inner_html: str, style: str) -> str:
    if not inner_html:
        return ""
    if style == "stripe":
        head = (
            '<div class="stripe-head">'
            f'<span class="label">{esc(title)}</span>'
            '<span class="line"></span>'
            "</div>"
        )
        return f"<section>{head}{inner_html}</section>"
    return f"<section><h2>{esc(title)}</h2>{inner_html}</section>"


def build_experience(experience: list[dict], marker: str) -> str:
    blocks = []
    for item in experience or []:
        left = join_non_empty([item.get("role", ""), item.get("company", "")], " | ")
        right = join_non_empty([item.get("start_date", ""), item.get("end_date", "")], " - ")
        if item.get("location"):
            right = join_non_empty([right, item["location"]], " | ")
        blocks.append(
            '<article class="entry">'
            f"{render_entry_title(left, right)}"
            f"{render_list(item.get('bullets', []), marker)}"
            "</article>"
        )
    return "".join(blocks)


def build_projects(projects: list[dict], marker: str) -> str:
    blocks = []
    for item in projects or []:
        left = join_non_empty([item.get("name", ""), item.get("role", "")], " | ")
        right = join_non_empty([item.get("start_date", ""), item.get("end_date", "")], " - ")
        stack = ", ".join(item.get("stack", []))
        stack_html = f'<p class="meta">{esc(stack)}</p>' if stack else ""
        blocks.append(
            '<article class="entry">'
            f"{render_entry_title(left, right)}"
            f"{stack_html}"
            f"{render_list(item.get('bullets', []), marker)}"
            "</article>"
        )
    return "".join(blocks)


def build_education(education: list[dict]) -> str:
    blocks = []
    for item in education or []:
        left = join_non_empty([item.get("school", ""), item.get("degree", ""), item.get("major", "")], " | ")
        right = join_non_empty([item.get("start_date", ""), item.get("end_date", "")], " - ")
        coursework = ", ".join(item.get("coursework", []))
        honors = ", ".join(item.get("honors", []))
        meta = join_non_empty([coursework and f"主修课程: {coursework}", honors and f"荣誉: {honors}"], " | ")
        meta_html = f'<p class="meta">{esc(meta)}</p>' if meta else ""
        blocks.append('<article class="entry">' + render_entry_title(left, right) + meta_html + "</article>")
    return "".join(blocks)


def build_skills(skills: list[dict]) -> str:
    rows = []
    for group in skills or []:
        name = group.get("group", "")
        items = ", ".join(group.get("items", []))
        if name or items:
            rows.append(f'<p class="skill-row"><strong>{esc(name)}:</strong> {esc(items)}</p>')
    return "".join(rows)


def build_awards(awards: list[str]) -> str:
    if not awards:
        return ""
    return render_list(awards, "disc")


def build_additional(additional: dict) -> str:
    if not additional:
        return ""
    rows = []
    for key, label in (("languages", "语言"), ("volunteering", "志愿经历"), ("publications", "出版物")):
        values = additional.get(key, [])
        if values:
            rows.append(f'<p class="skill-row"><strong>{label}:</strong> {esc(", ".join(values))}</p>')
    return "".join(rows)


def contact_grid(profile: dict, with_icon: bool) -> str:
    items = [
        ("姓名", profile.get("name", ""), "👤"),
        ("电话", profile.get("phone", ""), "📞"),
        ("邮箱", profile.get("email", ""), "✉"),
        ("所在地", profile.get("location", ""), "📍"),
    ]
    links = profile.get("links", [])
    if links:
        items.append(("链接", " | ".join(links), "🔗"))

    rows = []
    for label, value, icon in items:
        if not value:
            continue
        prefix = f'<span class="icon">{icon}</span>' if with_icon else ""
        rows.append(
            '<div class="contact-item">'
            f"{prefix}<span class=\"k\">{esc(label)}:</span>"
            f"<span class=\"v\">{esc(value)}</span>"
            "</div>"
        )
    return "".join(rows)


def build_header(profile: dict, style: str) -> str:
    summary = profile.get("summary", "")
    summary_html = f'<p class="summary">{esc(summary)}</p>' if summary else ""
    title = profile.get("title", "")
    title_html = f'<p class="title">{esc(title)}</p>' if title else ""

    if style == "stripe":
        return (
            '<header class="hdr-stripe">'
            '<div class="left">'
            f"<h1>{esc(profile.get('name', ''))}</h1>"
            f"{title_html}"
            f"<div class=\"contact-grid\">{contact_grid(profile, True)}</div>"
            f"{summary_html}"
            "</div>"
            '<div class="photo-slot">'
            + (
                f'<img src="{esc(profile.get("photo_url", ""))}" alt="photo" />'
                if profile.get("photo_url")
                else '<div class="photo-placeholder">+</div>'
            )
            + '<button type="button" class="photo-upload-overlay" aria-label="上传头像或替换头像"><span class="plus">+</span><span class="txt">上传头像</span></button>'
            + "</div>"
            "</header>"
        )

    if style == "sidebar":
        return (
            '<header class="hdr-sidebar">'
            f"<h1>{esc(profile.get('name', ''))}</h1>"
            f"{title_html}"
            f"{summary_html}"
            "</header>"
        )

    # compact
    contact_line = join_non_empty([
        profile.get("phone", ""),
        profile.get("email", ""),
        profile.get("location", ""),
        " | ".join(profile.get("links", [])),
    ])
    photo_html = (
        f'<img src="{esc(profile.get("photo_url", ""))}" alt="photo" />'
        if profile.get("photo_url")
        else '<div class="photo-placeholder">+</div>'
    )
    return (
        '<header class="hdr-compact">'
        '<div class="compact-head-left">'
        f"<h1>{esc(profile.get('name', ''))}</h1>"
        f"{title_html}"
        f"<p class=\"contact-line\">{esc(contact_line)}</p>"
        f"{summary_html}"
        "</div>"
        '<div class="photo-slot compact-photo">'
        + photo_html
        + '<button type="button" class="photo-upload-overlay" aria-label="上传头像或替换头像"><span class="plus">+</span><span class="txt">上传头像</span></button>'
        + "</div>"
        "</header>"
    )


def css_for_style(tokens: dict, style: str) -> str:
    sidebar_fg = text_color_for_bg(tokens.get("sidebar_bg", "#1f1f1f"))
    return f"""
    @page {{ size: A4; margin: 9mm; }}
    :root {{
      --text-primary: {tokens['text_primary']};
      --text-secondary: {tokens['text_secondary']};
      --rule: {tokens['rule']};
      --accent: {tokens['accent']};
      --bg: {tokens['bg']};
      --sidebar-bg: {tokens.get('sidebar_bg', '#1f1f1f')};
      --sidebar-fg: {sidebar_fg};
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #ececec; color: var(--text-primary); font-family: {tokens['font']}; font-size: 10pt; line-height: 1.35; }}
    .page {{
      width: 210mm;
      height: 297mm;
      margin: 12px auto;
      background: var(--bg);
      box-shadow: 0 2px 14px rgba(0, 0, 0, 0.12);
      overflow: hidden;
    }}
    .page-inner {{
      position: relative;
      width: 100%;
      transform-origin: top center;
      padding-top: var(--pad-top, 3mm);
      padding-bottom: var(--pad-bottom, 3mm);
    }}
    h1 {{ margin: 0; font-size: 20pt; letter-spacing: 0.02em; }}
    h2 {{ margin: 0 0 4px 0; font-size: 12pt; }}
    .title {{ margin: 2px 0 4px 0; color: var(--text-secondary); font-weight: 600; }}
    .summary {{
      margin: 6px 0 0 0;
      color: var(--text-secondary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .entry {{ margin: 6px 0; }}
    .entry-title {{ display: flex; justify-content: space-between; gap: 8px; font-weight: 700; }}
    .entry-title .right {{ color: var(--text-secondary); white-space: nowrap; font-weight: 600; }}
    .meta {{ margin: 2px 0; font-size: 9pt; color: var(--text-secondary); text-wrap: pretty; line-break: strict; }}
    ul {{ margin: 2px 0 0 15px; padding: 0; }}
    .marker-arrow {{ list-style: none; margin-left: 0; padding-left: 0; }}
    .marker-arrow li {{ position: relative; padding-left: 14px; margin: 2px 0; }}
    .marker-arrow li::before {{ content: '▸'; position: absolute; left: 0; color: var(--accent); }}
    .marker-disc {{ list-style: disc; }}
    .skill-row {{ margin: 2px 0; text-wrap: pretty; line-break: strict; }}

    .stripe {{ padding: 8mm 9mm; }}
    .hdr-stripe {{ display: grid; grid-template-columns: minmax(0, 1fr) 110px; gap: 12px; align-items: start; margin-bottom: 7px; }}
    .hdr-stripe .left {{ min-width: 0; }}
    .contact-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 4px 10px; margin-top: 5px; }}
    .contact-item {{ min-width: 0; font-size: 9.4pt; display: flex; gap: 5px; align-items: baseline; }}
    .contact-item .icon {{ width: 14px; text-align: center; }}
    .photo-slot {{ position: relative; width: 110px; height: 132px; border: 1px solid var(--rule); background: #f3f3f3; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
    .photo-slot img {{ width: 100%; height: 100%; object-fit: cover; }}
    .photo-placeholder {{ color: #888; font-size: 9pt; }}
    .stripe section {{ margin-top: 8px; }}
    .stripe-head {{ display: flex; align-items: center; margin-bottom: 5px; }}
    .stripe-head .label {{ background: var(--accent); color: #fff; font-weight: 700; padding: 4px 12px; border-radius: 1px; }}
    .stripe-head .line {{ flex: 1; border-bottom: 2px solid var(--accent); margin-left: 6px; }}

    .compact {{ padding: 8mm 9mm; }}
    .hdr-compact {{ display: grid; grid-template-columns: 1fr 92px; gap: 8px; align-items: start; padding-bottom: 2px; margin-bottom: 6px; text-align: left; }}
    .compact-head-left {{ min-width: 0; }}
    .hdr-compact .title {{ letter-spacing: 0.05em; }}
    .contact-line {{ margin: 2px 0 0 0; font-size: 9.2pt; }}
    .compact-photo {{ width: 92px; height: 112px; justify-self: end; }}
    .compact section {{ margin-top: 6px; }}
    .compact h2 {{ border-bottom: 2px solid var(--rule); padding-bottom: 2px; }}
    .compact .entry-title {{ font-size: 10pt; }}
    .compact ul li {{ font-size: 9.3pt; }}

    .sidebar {{ padding: 0; position: relative; --sidebar-visual-width: 78mm; }}
    .sidebar::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: var(--sidebar-visual-width);
      background: var(--sidebar-bg);
      z-index: 0;
      pointer-events: none;
    }}
    .page.sidebar .page-inner {{ height: 100%; padding-top: 0; padding-bottom: 0; }}
    .sidebar-wrap {{ position: relative; z-index: 1; display: grid; grid-template-columns: 78mm minmax(0, 1fr); min-height: 100%; height: 100%; align-items: stretch; }}
    .side-left {{ background: transparent; color: var(--sidebar-fg); padding: 10mm 8mm; }}
    .side-left h3 {{ margin: 14px 0 8px 0; font-size: 12pt; letter-spacing: 0.18em; }}
    .side-left .rule {{ border-bottom: 1px solid currentColor; opacity: 0.45; margin: 8px 0 12px 0; }}
    .side-left .contact-item {{ font-size: 9.2pt; margin: 6px 0; display: block; line-height: 1.52; }}
    .side-left .k {{ opacity: 0.9; }}
    .side-left .v {{ margin-left: 4px; }}
    .side-left .skill-row {{ margin: 8px 0; line-height: 1.52; }}
    .side-left ul {{ margin-top: 8px; }}
    .side-left li {{ margin: 5px 0; line-height: 1.5; }}
    .side-left > h3 + .rule + div,
    .side-left > h3 + .rule + p,
    .side-left > h3 + .rule + ul {{
      margin-bottom: 14px;
    }}
    .profile-photo-circle {{ position: relative; width: 120px; height: 120px; border-radius: 50%; overflow: hidden; border: 3px solid rgba(255,255,255,0.85); margin: 0 auto 18px auto; background: rgba(255,255,255,0.2); display:flex; align-items:center; justify-content:center; font-size:9pt; }}
    .profile-photo-circle img {{ width: 100%; height: 100%; object-fit: cover; }}
    .side-right {{ min-width: 0; padding: 9mm 6mm 8mm 7mm; line-height: 1.48; }}
    .hdr-sidebar {{ margin-bottom: 8px; }}
    .side-right section {{ margin-top: 8px; }}
    .side-right h2 {{ border-bottom: 2px solid var(--accent); padding-bottom: 2px; }}
    .side-right .entry {{ margin-bottom: 7px; }}
    .side-right .entry-title {{ align-items: flex-start; gap: 10px; }}
    .side-right .entry-title .left {{ flex: 1; min-width: 0; line-height: 1.32; overflow-wrap: anywhere; }}
    .side-right .entry-title .right {{
      white-space: normal;
      text-align: right;
      max-width: 38%;
      min-width: 92px;
      line-height: 1.25;
      font-size: 9.2pt;
    }}
    .side-right .meta {{ line-height: 1.5; margin-top: 4px; }}
    .side-right li {{ line-height: 1.54; margin: 3px 0; }}

    @media print {{
      body {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        background: transparent;
      }}
      .page {{
        width: auto;
        height: auto;
        margin: 0;
        box-shadow: none;
      }}
    }}
    """


def render_stripe(data: dict) -> str:
    profile = data.get("profile", {})
    parts = [build_header(profile, "stripe")]
    parts.append(section_block("教育背景", build_education(data.get("education", [])), "stripe"))
    parts.append(section_block("实习/工作经历", build_experience(data.get("experience", []), "disc"), "stripe"))
    parts.append(section_block("项目经历", build_projects(data.get("projects", []), "disc"), "stripe"))
    parts.append(section_block("技能", build_skills(data.get("skills", [])), "stripe"))
    parts.append(section_block("荣誉/奖项", build_awards(data.get("awards", [])), "stripe"))
    parts.append(section_block("附加信息", build_additional(data.get("additional", {})), "stripe"))
    return '<main class="page stripe"><div class="page-inner">' + "".join(parts) + "</div></main>"


def render_compact(data: dict) -> str:
    profile = data.get("profile", {})
    parts = [build_header(profile, "compact")]
    parts.append(section_block("教育背景", build_education(data.get("education", [])), "compact"))
    parts.append(section_block("工作经历", build_experience(data.get("experience", []), "arrow"), "compact"))
    parts.append(section_block("项目经历", build_projects(data.get("projects", []), "arrow"), "compact"))
    parts.append(section_block("个人技能", build_skills(data.get("skills", [])), "compact"))
    parts.append(section_block("荣誉/奖项", build_awards(data.get("awards", [])), "compact"))
    parts.append(section_block("自我评价", build_additional(data.get("additional", {})), "compact"))
    return '<main class="page compact"><div class="page-inner">' + "".join(parts) + "</div></main>"


def render_sidebar(data: dict) -> str:
    profile = data.get("profile", {})
    photo = profile.get("photo_url", "")
    photo_html = f'<img src="{esc(photo)}" alt="photo" />' if photo else '<div class="photo-placeholder">+</div>'

    left = (
        '<aside class="side-left">'
        f'<div class="profile-photo-circle">{photo_html}<button type="button" class="photo-upload-overlay circle" aria-label="上传头像或替换头像"><span class="plus">+</span><span class="txt">上传头像</span></button></div>'
        '<h3>个人信息</h3><div class="rule"></div>'
        f"<div>{contact_grid(profile, False)}</div>"
        '<h3>技能奖项</h3><div class="rule"></div>'
        f"{build_skills(data.get('skills', []))}"
        "</aside>"
    )

    right_parts = [build_header(profile, "sidebar")]
    right_parts.append(section_block("教育经历", build_education(data.get("education", [])), "sidebar"))
    right_parts.append(section_block("工作经历", build_experience(data.get("experience", []), "disc"), "sidebar"))
    right_parts.append(section_block("项目经历", build_projects(data.get("projects", []), "disc"), "sidebar"))
    right_parts.append(section_block("荣誉/奖项", build_awards(data.get("awards", [])), "sidebar"))
    right_parts.append(section_block("附加信息", build_additional(data.get("additional", {})), "sidebar"))

    right = '<section class="side-right">' + "".join(right_parts) + "</section>"
    return '<main class="page sidebar"><div class="page-inner"><div class="sidebar-wrap">' + left + right + "</div></div></main>"


def build_html(data: dict, style: str, accent: str, sidebar_bg: str) -> str:
    style = STYLE_ALIASES.get(style, style)
    defaults = STYLE_DEFAULTS[style].copy()

    if style == "sidebar":
        # Sidebar style uses one unified color token:
        # left sidebar background + right section lines/graphic accents.
        color_from_accent = normalize_hex(accent, "")
        color_from_sidebar = normalize_hex(sidebar_bg, "")
        unified = color_from_sidebar or color_from_accent or defaults["accent"]
        defaults["accent"] = unified
        defaults["rule"] = unified
        defaults["sidebar_bg"] = unified
    else:
        defaults["accent"] = normalize_hex(accent, defaults["accent"])
        # Keep section lines/graphics consistent with the selected theme color.
        defaults["rule"] = defaults["accent"]

    if style == "stripe":
        body = render_stripe(data)
    elif style == "compact":
        body = render_compact(data)
    else:
        body = render_sidebar(data)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(data.get('profile', {}).get('name', 'Resume'))}</title>
  <style>{css_for_style(defaults, style)}</style>
</head>
<body>
<div class="editor-toolbar" id="editorToolbar">
  <div class="theme-palette" id="themePalette" aria-label="快捷配色">
    <button type="button" class="theme-dot active" data-color="#111111" title="经典黑" aria-label="经典黑"></button>
    <button type="button" class="theme-dot" data-color="#1f4e8c" title="商务蓝" aria-label="商务蓝"></button>
    <button type="button" class="theme-dot" data-color="#0f766e" title="青绿色" aria-label="青绿色"></button>
    <button type="button" class="theme-dot" data-color="#475569" title="石墨灰蓝" aria-label="石墨灰蓝"></button>
    <button type="button" class="theme-dot" data-color="#be123c" title="酒红色" aria-label="酒红色"></button>
  </div>
  <button type="button" id="editToggleBtn"><svg viewBox="0 0 24 24" class="icon-svg" aria-hidden="true"><path d="M4 20h4l10-10-4-4L4 16v4z"></path><path d="M13 7l4 4"></path></svg><span class="btn-text">开始编辑</span></button>
  <button type="button" id="downloadPdfBtn"><svg viewBox="0 0 24 24" class="icon-svg" aria-hidden="true"><path d="M12 3v11"></path><path d="M8 10l4 4 4-4"></path><path d="M4 20h16"></path></svg><span class="btn-text">下载PDF</span></button>
  <div class="save-wrap">
    <button type="button" id="saveCopyBtn"><svg viewBox="0 0 24 24" class="icon-svg" aria-hidden="true"><path d="M5 4h11l3 3v13H5z"></path><path d="M8 4v6h8V4"></path><path d="M8 17h8"></path></svg><span class="btn-text">保存副本</span></button>
    <small>修改后需要保存副本</small>
  </div>
  <input type="file" id="photoFileInput" accept="image/*" hidden />
</div>
<aside class="outline-panel" id="outlinePanel">
  <div class="outline-title"><svg viewBox="0 0 24 24" class="icon-svg" aria-hidden="true"><path d="M4 5h13v14H4z"></path><path d="M17 7h3v12h-3"></path><path d="M7 9h7"></path><path d="M7 13h7"></path></svg><span>大纲预览</span></div>
  <div class="outline-tip">可拖拽调整顺序</div>
  <div class="outline-list" id="outlineList"></div>
  <div class="outline-actions">
    <button type="button" id="addSectionBtn"><svg viewBox="0 0 24 24" class="icon-svg" aria-hidden="true"><path d="M12 5v14"></path><path d="M5 12h14"></path></svg><span>添加模块</span></button>
  </div>
  <div class="deleted-bucket" id="deletedBucket">
    <div class="deleted-title">已删除内容</div>
    <div class="deleted-list" id="deletedList"></div>
  </div>
  <div class="outline-note">调整后请点击右侧“保存副本”</div>
</aside>
<div class="print-modal-backdrop hidden" id="printModalBackdrop"></div>
<div class="print-modal hidden" id="printModal" role="dialog" aria-modal="true" aria-labelledby="printModalTitle">
  <div class="print-tip-title" id="printModalTitle">打印前请确认</div>
  <div>1. 纸张：A4</div>
  <div>2. 背景图形：开启</div>
  <div>3. 页眉页脚：关闭</div>
  <div class="print-modal-actions">
    <button type="button" id="cancelPrintBtn" class="btn-secondary">取消</button>
    <button type="button" id="confirmPrintBtn" class="btn-primary">确认并打开打印</button>
  </div>
</div>
{body}
<script>
(function() {{
  function fitA4() {{
    var page = document.querySelector('.page');
    var inner = document.querySelector('.page-inner');
    if (!page || !inner) return;
    var isSidebarPage = page.classList.contains('sidebar');
    var sideLeft = document.querySelector('.side-left');
    var sideRight = document.querySelector('.side-right');

    inner.style.transform = 'scale(1)';
    inner.style.width = '100%';
    inner.style.marginLeft = '0';
    inner.style.transformOrigin = isSidebarPage ? 'top left' : 'top center';
    page.style.setProperty('--sidebar-visual-width', '78mm');
    inner.style.setProperty('--pad-top', isSidebarPage ? '0mm' : '3mm');
    inner.style.setProperty('--pad-bottom', isSidebarPage ? '0mm' : '3mm');

    if (sideLeft) {{
      sideLeft.style.transform = 'scale(1)';
      sideLeft.style.transformOrigin = 'top left';
      sideLeft.style.width = 'auto';
    }}
    if (sideRight) {{
      sideRight.style.transform = 'scale(1)';
      sideRight.style.transformOrigin = 'top left';
      sideRight.style.width = 'auto';
    }}

    var pageHeight = page.clientHeight;
    var contentHeight = inner.scrollHeight;
    if (isSidebarPage) {{
      var leftH = sideLeft ? sideLeft.scrollHeight : 0;
      var rightH = sideRight ? sideRight.scrollHeight : 0;
      contentHeight = Math.max(leftH, rightH, inner.scrollHeight);
    }}
    var density = contentHeight / pageHeight;

    // Adaptive breathing space:
    // Dense content -> smaller top/bottom space
    // Sparse content -> larger breathing space
    if (!isSidebarPage) {{
      if (density > 0.9) {{
        inner.style.setProperty('--pad-top', '1.5mm');
        inner.style.setProperty('--pad-bottom', '1.5mm');
      }} else if (density < 0.7) {{
        inner.style.setProperty('--pad-top', '5mm');
        inner.style.setProperty('--pad-bottom', '5mm');
      }}
    }}

    if (isSidebarPage) {{
      var leftH2 = sideLeft ? sideLeft.scrollHeight : 0;
      var rightH2 = sideRight ? sideRight.scrollHeight : 0;
      contentHeight = Math.max(leftH2, rightH2, inner.scrollHeight);
    }} else {{
      contentHeight = inner.scrollHeight;
    }}
    density = contentHeight / pageHeight;

    var safeTop = isSidebarPage ? 0 : (density > 0.9 ? 4 : 8);
    var safeBottom = isSidebarPage ? 0 : (density > 0.9 ? 6 : 10);
    var targetHeight = Math.max(0, pageHeight - safeTop - safeBottom);

    if (contentHeight <= targetHeight) return;

    var ratio = targetHeight / contentHeight;
    ratio = Math.max(0.72, Math.min(1, ratio));

    if (isSidebarPage && sideLeft && sideRight) {{
      // Sidebar mode hard rule: left/right columns remain fixed and never overlap.
      // Shrink both columns consistently when overflowing vertically.
      sideLeft.style.transform = 'scale(' + ratio + ')';
      sideLeft.style.width = (100 / ratio).toFixed(4) + '%';
      sideRight.style.transform = 'scale(' + ratio + ')';
      sideRight.style.width = (100 / ratio).toFixed(4) + '%';
    }} else {{
      inner.style.transform = 'scale(' + ratio + ')';
      inner.style.width = '100%';
    }}

    // One more pass for rounding
    var currentHeight = inner.getBoundingClientRect().height;
    if (isSidebarPage && sideLeft && sideRight) {{
      currentHeight = Math.max(sideLeft.getBoundingClientRect().height, sideRight.getBoundingClientRect().height);
    }}
    if (currentHeight > targetHeight) {{
      var retry = ratio * 0.98;
      if (isSidebarPage && sideLeft && sideRight) {{
        sideLeft.style.transform = 'scale(' + retry + ')';
        sideLeft.style.width = (100 / retry).toFixed(4) + '%';
        sideRight.style.transform = 'scale(' + retry + ')';
        sideRight.style.width = (100 / retry).toFixed(4) + '%';
      }} else {{
        inner.style.transform = 'scale(' + retry + ')';
        inner.style.width = '100%';
      }}
    }}
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', function() {{
      clampSummaryToOneLine();
      applyWidowControl();
      fitA4();
    }});
  }} else {{
    clampSummaryToOneLine();
    applyWidowControl();
    fitA4();
  }}
  window.addEventListener('resize', function() {{
    clampSummaryToOneLine();
    applyWidowControl();
    fitA4();
  }});

  var isEditMode = false;
  var toolbar = document.getElementById('editorToolbar');
  var editBtn = document.getElementById('editToggleBtn');
  var pdfBtn = document.getElementById('downloadPdfBtn');
  var printModal = document.getElementById('printModal');
  var printBackdrop = document.getElementById('printModalBackdrop');
  var confirmPrintBtn = document.getElementById('confirmPrintBtn');
  var cancelPrintBtn = document.getElementById('cancelPrintBtn');
  var outlineList = document.getElementById('outlineList');
  var addSectionBtn = document.getElementById('addSectionBtn');
  var deletedList = document.getElementById('deletedList');
  var themePalette = document.getElementById('themePalette');
  var fileInput = document.getElementById('photoFileInput');
  var saveBtn = document.getElementById('saveCopyBtn');
  var draggingItem = null;
  var deletedStore = [];
  var editableSelector = '.page h1, .page h2, .page h3, .page p, .page li, .page .left, .page .right, .page .label, .page .k, .page .v';

  function sanitizeFilePart(text) {{
    return (text || '候选人')
      .replace(/[\\\\/:*?\"<>|]/g, '')
      .replace(/\\s+/g, '')
      .trim() || '候选人';
  }}

  function todayYYYYMMDD() {{
    var d = new Date();
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return '' + y + m + day;
  }}

  function getResumeBaseName() {{
    var nameNode = document.querySelector('.page h1');
    var name = sanitizeFilePart(nameNode ? nameNode.textContent : '候选人');
    var page = document.querySelector('.page');
    var styleTag = 'stripe';
    if (page) {{
      if (page.classList.contains('sidebar')) styleTag = 'sidebar';
      else if (page.classList.contains('compact')) styleTag = 'compact';
      else if (page.classList.contains('stripe')) styleTag = 'stripe';
    }}
    return name + '-个人简历-' + styleTag + '-' + todayYYYYMMDD();
  }}

  function setPaletteActive(color) {{
    if (!themePalette) return;
    var target = (color || '').toLowerCase();
    var chips = themePalette.querySelectorAll('.theme-dot');
    chips.forEach(function(chip) {{
      var c = (chip.getAttribute('data-color') || '').toLowerCase();
      chip.classList.toggle('active', c === target);
    }});
  }}

  function applyThemeColor(color) {{
    if (!color) return;
    var page = document.querySelector('.page');
    var root = document.documentElement;
    root.style.setProperty('--accent', color);
    root.style.setProperty('--rule', color);
    if (page && page.classList.contains('sidebar')) {{
      function luminance(hex) {{
        var h = (hex || '').replace('#', '');
        if (h.length === 3) {{
          h = h.split('').map(function(ch) {{ return ch + ch; }}).join('');
        }}
        if (!/^[0-9a-fA-F]{6}$/.test(h)) return 0;
        var r = parseInt(h.slice(0, 2), 16);
        var g = parseInt(h.slice(2, 4), 16);
        var b = parseInt(h.slice(4, 6), 16);
        return 0.299 * r + 0.587 * g + 0.114 * b;
      }}
      root.style.setProperty('--sidebar-bg', color);
      var sidebarFg = luminance(color) < 150 ? '#ffffff' : '#111111';
      root.style.setProperty('--sidebar-fg', sidebarFg);
      var sideLeft = document.querySelector('.side-left');
      if (sideLeft) {{
        sideLeft.style.color = sidebarFg;
      }}
    }}
    setPaletteActive(color);
  }}

  function clampSummaryToOneLine() {{
    if (isEditMode) return;
    var summary = document.querySelector('.summary');
    if (!summary) return;

    var raw = (summary.getAttribute('data-original-summary') || summary.textContent || '').trim();
    if (!raw) return;
    summary.setAttribute('data-original-summary', raw);
    summary.textContent = raw;

    if (summary.scrollWidth <= summary.clientWidth) return;

    var text = raw.replace(/[，。；、\\s]+$/g, '');
    var low = 1;
    var high = text.length;
    var best = '';

    while (low <= high) {{
      var mid = Math.floor((low + high) / 2);
      var candidate = text.slice(0, mid) + '…';
      summary.textContent = candidate;
      if (summary.scrollWidth <= summary.clientWidth) {{
        best = candidate;
        low = mid + 1;
      }} else {{
        high = mid - 1;
      }}
    }}

    summary.textContent = best || (text.slice(0, 1) + '…');
    summary.title = raw;
  }}

  function getLineRects(el) {{
    var range = document.createRange();
    range.selectNodeContents(el);
    var rects = Array.prototype.slice.call(range.getClientRects());
    return rects.filter(function(r) {{ return r.width > 0 && r.height > 0; }});
  }}

  function minLineRatio(rects, lineWidth) {{
    if (!rects.length || lineWidth <= 0) return 1;
    var min = 1;
    rects.forEach(function(r) {{
      var ratio = r.width / lineWidth;
      if (ratio < min) min = ratio;
    }});
    return min;
  }}

  function tuneLineBalance(el) {{
    if (!el || el.offsetParent === null) return;
    el.style.letterSpacing = '';
    el.style.wordSpacing = '';
    el.style.fontSize = '';

    var lineWidth = Math.max(1, el.clientWidth);
    var rects = getLineRects(el);
    if (rects.length < 2) return;

    // If any wrapped line is too short (including middle/last), tighten first.
    var threshold = 0.22;
    var currentMin = minLineRatio(rects, lineWidth);
    if (currentMin >= threshold) return;

    var tightenSteps = [0, -0.008, -0.016, -0.024, -0.032, -0.04, -0.05, -0.058];
    for (var i = 0; i < tightenSteps.length; i += 1) {{
      var step = tightenSteps[i];
      el.style.letterSpacing = step.toFixed(3) + 'em';
      el.style.wordSpacing = (step * 0.55).toFixed(3) + 'em';
      rects = getLineRects(el);
      currentMin = minLineRatio(rects, lineWidth);
      if (currentMin >= threshold) return;
    }}

    // If still bad, slightly shrink font size for this block only.
    var baseSize = parseFloat(window.getComputedStyle(el).fontSize || '16');
    if (!isFinite(baseSize)) return;
    var shrinkSteps = [0.2, 0.35, 0.5, 0.65];
    for (var j = 0; j < shrinkSteps.length; j += 1) {{
      el.style.fontSize = (baseSize - shrinkSteps[j]).toFixed(2) + 'px';
      rects = getLineRects(el);
      currentMin = minLineRatio(rects, lineWidth);
      if (currentMin >= threshold) return;
    }}
  }}

  function applyWidowControl() {{
    var targets = document.querySelectorAll('.entry li, .entry .meta, .skill-row, .summary, .contact-line');
    targets.forEach(tuneLineBalance);
  }}

  function setEditMode(enable) {{
    isEditMode = enable;
    var nodes = document.querySelectorAll(editableSelector);
    nodes.forEach(function(node) {{
      node.setAttribute('contenteditable', enable ? 'true' : 'false');
      if (enable) {{
        node.classList.add('editable-node');
      }} else {{
        node.classList.remove('editable-node');
      }}
    }});
    document.body.classList.toggle('is-editing', enable);
    var editText = editBtn.querySelector('.btn-text');
    if (editText) editText.textContent = enable ? '完成编辑' : '开始编辑';
    if (!enable) {{
      clampSummaryToOneLine();
      applyWidowControl();
    }}
    fitA4();
  }}

  function getResumeSections() {{
    var sideRight = document.querySelector('.side-right');
    if (sideRight) {{
      return Array.prototype.slice.call(sideRight.children).filter(function(n) {{
        return n.tagName && n.tagName.toLowerCase() === 'section';
      }});
    }}
    return Array.prototype.slice.call(document.querySelectorAll('.page-inner > section'));
  }}

  function getSectionTitle(section) {{
    var label = section.querySelector('.stripe-head .label');
    if (label) return (label.textContent || '').trim();
    var h2 = section.querySelector('h2');
    if (h2) return (h2.textContent || '').trim();
    return '未命名模块';
  }}

  function getSectionEntries(section) {{
    return Array.prototype.slice.call(section.children).filter(function(n) {{
      return n.classList && n.classList.contains('entry');
    }});
  }}

  function getEntryTitle(entry) {{
    var left = entry.querySelector('.entry-title .left');
    var text = left ? (left.textContent || '').trim() : (entry.textContent || '').trim();
    if (text.length > 28) text = text.slice(0, 28) + '…';
    return text || '条目';
  }}

  function ensureOutlineIds() {{
    getResumeSections().forEach(function(section, sIdx) {{
      if (!section.dataset.sid) section.dataset.sid = 's-' + sIdx;
      getSectionEntries(section).forEach(function(entry, eIdx) {{
        if (!entry.dataset.eid) entry.dataset.eid = section.dataset.sid + '-e-' + eIdx;
      }});
    }});
  }}

  function rebuildOutline() {{
    if (!outlineList) return;
    ensureOutlineIds();
    outlineList.innerHTML = '';

    getResumeSections().forEach(function(section) {{
      var secNode = document.createElement('div');
      secNode.className = 'outline-section-item';
      secNode.draggable = true;
      secNode.dataset.outlineType = 'section';
      secNode.dataset.sid = section.dataset.sid;
      secNode.innerHTML = '<span class=\"drag\"><svg viewBox=\"0 0 24 24\" class=\"icon-handle\" aria-hidden=\"true\"><circle cx=\"9\" cy=\"7\" r=\"1.4\"></circle><circle cx=\"15\" cy=\"7\" r=\"1.4\"></circle><circle cx=\"9\" cy=\"12\" r=\"1.4\"></circle><circle cx=\"15\" cy=\"12\" r=\"1.4\"></circle><circle cx=\"9\" cy=\"17\" r=\"1.4\"></circle><circle cx=\"15\" cy=\"17\" r=\"1.4\"></circle></svg></span><span class=\"outline-text\">' + getSectionTitle(section) + '</span><button type=\"button\" class=\"outline-delete\" data-delete-type=\"section\" data-sid=\"' + section.dataset.sid + '\" aria-label=\"删除模块\"><svg viewBox=\"0 0 24 24\" class=\"icon-svg\" aria-hidden=\"true\"><path d=\"M6 7h12\"></path><path d=\"M9 7v12\"></path><path d=\"M15 7v12\"></path><path d=\"M10 4h4\"></path><path d=\"M7 7l1 13h8l1-13\"></path></svg></button>';
      outlineList.appendChild(secNode);

      var entries = getSectionEntries(section);
      if (entries.length) {{
        var group = document.createElement('div');
        group.className = 'outline-entry-group';
        entries.forEach(function(entry) {{
          var item = document.createElement('div');
          item.className = 'outline-entry-item';
          item.draggable = true;
          item.dataset.outlineType = 'entry';
          item.dataset.sid = section.dataset.sid;
          item.dataset.eid = entry.dataset.eid;
          item.innerHTML = '<span class=\"drag\"><svg viewBox=\"0 0 24 24\" class=\"icon-handle\" aria-hidden=\"true\"><circle cx=\"9\" cy=\"7\" r=\"1.4\"></circle><circle cx=\"15\" cy=\"7\" r=\"1.4\"></circle><circle cx=\"9\" cy=\"12\" r=\"1.4\"></circle><circle cx=\"15\" cy=\"12\" r=\"1.4\"></circle><circle cx=\"9\" cy=\"17\" r=\"1.4\"></circle><circle cx=\"15\" cy=\"17\" r=\"1.4\"></circle></svg></span><span class=\"outline-text\">' + getEntryTitle(entry) + '</span><button type=\"button\" class=\"outline-delete\" data-delete-type=\"entry\" data-eid=\"' + entry.dataset.eid + '\" aria-label=\"删除条目\"><svg viewBox=\"0 0 24 24\" class=\"icon-svg\" aria-hidden=\"true\"><path d=\"M6 7h12\"></path><path d=\"M9 7v12\"></path><path d=\"M15 7v12\"></path><path d=\"M10 4h4\"></path><path d=\"M7 7l1 13h8l1-13\"></path></svg></button>';
          group.appendChild(item);
        }});
        outlineList.appendChild(group);
      }}
    }});
  }}

  function syncAfterReorder() {{
    rebuildOutline();
    renderDeletedList();
    clampSummaryToOneLine();
    applyWidowControl();
    fitA4();
  }}

  function findSectionById(sid) {{
    return document.querySelector('.page section[data-sid=\"' + sid + '\"]');
  }}

  function findEntryById(eid) {{
    return document.querySelector('.page article.entry[data-eid=\"' + eid + '\"]');
  }}

  function getSectionsContainer() {{
    var sideRight = document.querySelector('.side-right');
    if (sideRight) return sideRight;
    return document.querySelector('.page-inner');
  }}

  function renderDeletedList() {{
    if (!deletedList) return;
    deletedList.innerHTML = '';
    if (!deletedStore.length) {{
      deletedList.innerHTML = '<div class="deleted-empty">暂无</div>';
      return;
    }}
    deletedStore.forEach(function(item) {{
      var row = document.createElement('div');
      row.className = 'deleted-item';
      row.innerHTML = '<span class="deleted-text" title="' + item.label + '">' + item.label + '</span>' +
        '<button type="button" class="undo-delete-btn" data-delid="' + item.id + '">撤销</button>';
      deletedList.appendChild(row);
    }});
  }}

  function parseElement(html) {{
    var tpl = document.createElement('template');
    tpl.innerHTML = html.trim();
    return tpl.content.firstElementChild;
  }}

  function recordDeleted(payload) {{
    payload.id = 'del-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7);
    deletedStore.unshift(payload);
    if (deletedStore.length > 20) deletedStore = deletedStore.slice(0, 20);
    renderDeletedList();
  }}

  function restoreDeleted(delId) {{
    var idx = deletedStore.findIndex(function(x) {{ return x.id === delId; }});
    if (idx < 0) return;
    var item = deletedStore[idx];
    deletedStore.splice(idx, 1);

    var node = parseElement(item.html);
    if (!node) {{
      renderDeletedList();
      return;
    }}

    if (item.type === 'section') {{
      var container = getSectionsContainer();
      if (!container) return;
      var beforeSection = item.nextSid ? findSectionById(item.nextSid) : null;
      if (beforeSection) container.insertBefore(node, beforeSection);
      else container.appendChild(node);
      syncAfterReorder();
      return;
    }}

    if (item.type === 'entry') {{
      var section = findSectionById(item.sid || '');
      if (!section) {{
        renderDeletedList();
        return;
      }}
      var beforeEntry = item.nextEid ? findEntryById(item.nextEid) : null;
      if (beforeEntry && beforeEntry.parentNode === section) section.insertBefore(node, beforeEntry);
      else section.appendChild(node);
      syncAfterReorder();
      return;
    }}
  }}

  function buildNewSectionElement(title) {{
    var page = document.querySelector('.page');
    var sec = document.createElement('section');
    var t = (title || '新增模块').trim() || '新增模块';
    if (page && page.classList.contains('stripe')) {{
      sec.innerHTML =
        '<div class=\"stripe-head\"><span class=\"label\">' + t + '</span><span class=\"line\"></span></div>' +
        '<article class=\"entry\" data-generated=\"true\">' +
        '<div class=\"entry-title\"><div class=\"left\">请填写小标题</div><div class=\"right\"></div></div>' +
        '<ul class=\"marker-disc\"><li>请填写内容</li></ul>' +
        '</article>';
      return sec;
    }}
    var marker = page && page.classList.contains('compact') ? 'marker-arrow' : 'marker-disc';
    sec.innerHTML =
      '<h2>' + t + '</h2>' +
      '<article class=\"entry\" data-generated=\"true\">' +
      '<div class=\"entry-title\"><div class=\"left\">请填写小标题</div><div class=\"right\"></div></div>' +
      '<ul class=\"' + marker + '\"><li>请填写内容</li></ul>' +
      '</article>';
    return sec;
  }}

  if (outlineList) {{
    outlineList.addEventListener('dragstart', function(e) {{
      var item = e.target.closest('[data-outline-type]');
      if (!item) return;
      draggingItem = {{
        type: item.dataset.outlineType,
        sid: item.dataset.sid || '',
        eid: item.dataset.eid || ''
      }};
      item.classList.add('dragging');
      if (e.dataTransfer) {{
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', JSON.stringify(draggingItem));
      }}
    }});

    outlineList.addEventListener('dragend', function(e) {{
      var item = e.target.closest('[data-outline-type]');
      if (item) item.classList.remove('dragging');
      draggingItem = null;
      Array.prototype.slice.call(outlineList.querySelectorAll('.drag-over')).forEach(function(n) {{
        n.classList.remove('drag-over');
      }});
    }});

    outlineList.addEventListener('dragover', function(e) {{
      var target = e.target.closest('[data-outline-type]');
      if (!draggingItem || !target) return;
      e.preventDefault();
      Array.prototype.slice.call(outlineList.querySelectorAll('.drag-over')).forEach(function(n) {{
        n.classList.remove('drag-over');
      }});
      target.classList.add('drag-over');
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
    }});

    outlineList.addEventListener('drop', function(e) {{
      var target = e.target.closest('[data-outline-type]');
      if (!draggingItem || !target) return;
      e.preventDefault();

      if (draggingItem.type === 'section' && target.dataset.outlineType === 'section') {{
        if (draggingItem.sid === target.dataset.sid) return;
        var fromSection = findSectionById(draggingItem.sid);
        var toSection = findSectionById(target.dataset.sid);
        if (fromSection && toSection) {{
          toSection.parentNode.insertBefore(fromSection, toSection);
          syncAfterReorder();
        }}
        return;
      }}

      if (draggingItem.type === 'entry' && target.dataset.outlineType === 'entry') {{
        if (draggingItem.eid === target.dataset.eid) return;
        var fromEntry = findEntryById(draggingItem.eid);
        var toEntry = findEntryById(target.dataset.eid);
        if (fromEntry && toEntry && toEntry.parentNode) {{
          toEntry.parentNode.insertBefore(fromEntry, toEntry);
          syncAfterReorder();
        }}
      }}
    }});

    outlineList.addEventListener('click', function(e) {{
      var btn = e.target.closest('.outline-delete');
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();

      var delType = btn.dataset.deleteType;
      if (delType === 'section') {{
        var s = findSectionById(btn.dataset.sid || '');
        if (s) {{
          var title = getSectionTitle(s);
          var next = s.nextElementSibling;
          var nextSid = next && next.dataset ? (next.dataset.sid || '') : '';
          recordDeleted({{
            type: 'section',
            label: title,
            html: s.outerHTML,
            nextSid: nextSid
          }});
          s.remove();
          syncAfterReorder();
        }}
        return;
      }}

      if (delType === 'entry') {{
        var entry = findEntryById(btn.dataset.eid || '');
        if (entry) {{
          var sid = entry.closest('section') && entry.closest('section').dataset ? entry.closest('section').dataset.sid : '';
          var nextEntry = entry.nextElementSibling;
          var nextEid = nextEntry && nextEntry.dataset ? (nextEntry.dataset.eid || '') : '';
          recordDeleted({{
            type: 'entry',
            label: getEntryTitle(entry),
            html: entry.outerHTML,
            sid: sid,
            nextEid: nextEid
          }});
          entry.remove();
          syncAfterReorder();
        }}
      }}
    }});
  }}

  if (deletedList) {{
    deletedList.addEventListener('click', function(e) {{
      var btn = e.target.closest('.undo-delete-btn');
      if (!btn) return;
      restoreDeleted(btn.dataset.delid || '');
    }});
  }}

  if (addSectionBtn) {{
    addSectionBtn.addEventListener('click', function() {{
      var title = window.prompt('请输入模块名称', '新增模块');
      if (title === null) return;
      var container = getSectionsContainer();
      if (!container) return;
      var sec = buildNewSectionElement(title);
      container.appendChild(sec);
      syncAfterReorder();
      setEditMode(true);
    }});
  }}

  function downloadCurrentHtml() {{
    if (isEditMode) {{
      setEditMode(false);
    }}
    var html = '<!doctype html>\\n' + document.documentElement.outerHTML;
    var blob = new Blob([html], {{ type: 'text/html;charset=utf-8' }});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = getResumeBaseName() + '.html';
    document.body.appendChild(a);
    a.click();
    a.remove();

    if (window.confirm('副本已下载，是否在新标签页打开预览？')) {{
      window.open(url, '_blank');
    }}

    setTimeout(function() {{
      URL.revokeObjectURL(url);
    }}, 20000);
  }}

  function setPhoto(srcData) {{
    if (!srcData) return;
    var slots = document.querySelectorAll('.photo-slot, .profile-photo-circle');
    if (!slots.length) {{
      alert('当前模板没有头像区域。请切换到含头像模板（如 stripe 或 sidebar）。');
      return;
    }}
    slots.forEach(function(slot) {{
      var isCircle = slot.classList.contains('profile-photo-circle');
      slot.innerHTML = '<img src=\"' + srcData + '\" alt=\"photo\" />' +
        (isCircle
          ? '<button type=\"button\" class=\"photo-upload-overlay circle\" aria-label=\"上传头像或替换头像\"><span class=\"plus\">+</span><span class=\"txt\">替换头像</span></button>'
          : '<button type=\"button\" class=\"photo-upload-overlay\" aria-label=\"上传头像或替换头像\"><span class=\"plus\">+</span><span class=\"txt\">替换头像</span></button>');
    }});
    bindPhotoHotspots();
    fitA4();
  }}

  function readPhotoFile(file) {{
    if (!file) return;
    if (!file.type || !file.type.startsWith('image/')) {{
      alert('请选择图片文件。');
      return;
    }}
    var reader = new FileReader();
    reader.onload = function(e) {{
      setPhoto(e.target.result);
    }};
    reader.readAsDataURL(file);
  }}

  function bindPhotoHotspots() {{
    var slots = document.querySelectorAll('.photo-slot, .profile-photo-circle');
    slots.forEach(function(slot) {{
      slot.style.cursor = 'pointer';
      slot.onclick = function() {{
        fileInput.click();
      }};
      var overlay = slot.querySelector('.photo-upload-overlay');
      if (overlay) {{
        overlay.onclick = function(e) {{
          e.stopPropagation();
          fileInput.click();
        }};
      }}
    }});
  }}

  editBtn.addEventListener('click', function() {{
    setEditMode(!isEditMode);
  }});
  fileInput.addEventListener('change', function() {{
    if (fileInput.files && fileInput.files[0]) {{
      readPhotoFile(fileInput.files[0]);
    }}
    fileInput.value = '';
  }});
  if (themePalette) {{
    themePalette.addEventListener('click', function(e) {{
      var btn = e.target.closest('.theme-dot');
      if (!btn) return;
      applyThemeColor(btn.getAttribute('data-color'));
    }});
  }}
  saveBtn.addEventListener('click', downloadCurrentHtml);
  function openPrintModal() {{
    if (!printModal || !printBackdrop) return;
    printBackdrop.classList.remove('hidden');
    printModal.classList.remove('hidden');
  }}

  function closePrintModal() {{
    if (!printModal || !printBackdrop) return;
    printBackdrop.classList.add('hidden');
    printModal.classList.add('hidden');
  }}

  pdfBtn.addEventListener('click', function() {{
    if (isEditMode) {{
      setEditMode(false);
    }}
    document.title = getResumeBaseName();
    openPrintModal();
  }});
  confirmPrintBtn.addEventListener('click', function() {{
    closePrintModal();
    window.print();
  }});
  cancelPrintBtn.addEventListener('click', closePrintModal);
  printBackdrop.addEventListener('click', closePrintModal);
  document.title = getResumeBaseName();
  bindPhotoHotspots();
  setPaletteActive((getComputedStyle(document.documentElement).getPropertyValue('--accent') || '').trim());
  rebuildOutline();
  renderDeletedList();
}})();
</script>
<style>
  .editor-toolbar {{
    position: fixed;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    width: 148px;
    z-index: 9999;
  }}
  .theme-palette {{
    width: 148px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 8px;
    border-radius: 10px;
    background: #ffffff;
    border: 1px solid #dbe3ef;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.08);
  }}
  .theme-dot {{
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 999px;
    border: 2px solid #d1d5db;
    cursor: pointer;
    padding: 0;
    margin: 0;
    flex-shrink: 0;
    background: var(--dot, #111111);
    display: inline-block;
  }}
  .theme-dot[data-color="#111111"] {{ --dot: #111111; }}
  .theme-dot[data-color="#1f4e8c"] {{ --dot: #1f4e8c; }}
  .theme-dot[data-color="#0f766e"] {{ --dot: #0f766e; }}
  .theme-dot[data-color="#475569"] {{ --dot: #475569; }}
  .theme-dot[data-color="#be123c"] {{ --dot: #be123c; }}
  .theme-dot.active {{
    border-color: #111827;
    box-shadow: 0 0 0 2px rgba(17, 24, 39, 0.15);
  }}
  .editor-toolbar > button,
  .editor-toolbar .save-wrap > button {{
    border: 0;
    border-radius: 8px;
    width: 148px;
    height: 44px;
    padding: 0 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    background: #111827;
    color: #fff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }}
  .editor-toolbar > button:hover,
  .editor-toolbar .save-wrap > button:hover {{
    opacity: 0.92;
  }}
  .outline-panel {{
    position: fixed;
    left: 20px;
    top: 20px;
    width: 280px;
    max-height: calc(100vh - 40px);
    overflow: auto;
    background: #ffffff;
    border: 1px solid #dbe3ef;
    border-radius: 10px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.1);
    padding: 10px;
    z-index: 9999;
  }}
  .outline-title {{
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .outline-tip {{
    font-size: 12px;
    color: #475569;
    margin-bottom: 8px;
  }}
  .outline-list {{
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .outline-section-item,
  .outline-entry-item {{
    border: 1px solid #dbe3ef;
    border-radius: 8px;
    background: #f8fafc;
    font-size: 12px;
    line-height: 1.3;
    padding: 6px 7px;
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: grab;
    position: relative;
  }}
  .outline-section-item .outline-text {{
    font-weight: 700;
  }}
  .outline-entry-item .outline-text {{
    font-weight: 500;
  }}
  .outline-entry-group {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-left: 10px;
  }}
  .outline-text {{
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .outline-section-item .drag,
  .outline-entry-item .drag {{
    color: #64748b;
    font-size: 12px;
    width: 14px;
    text-align: center;
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }}
  .icon-svg {{
    width: 15px;
    height: 15px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
    flex-shrink: 0;
  }}
  .icon-handle {{
    width: 12px;
    height: 12px;
    fill: currentColor;
  }}
  .drag-over {{
    outline: 2px dashed #3b82f6;
    outline-offset: 1px;
  }}
  .outline-note {{
    margin-top: 8px;
    font-size: 11px;
    color: #64748b;
  }}
  .outline-actions {{
    margin-top: 8px;
  }}
  .outline-actions button {{
    width: 100%;
    border: 1px dashed #94a3b8;
    background: #f8fafc;
    color: #334155;
    border-radius: 8px;
    height: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    cursor: pointer;
  }}
  .deleted-bucket {{
    margin-top: 8px;
    border-top: 1px solid #e2e8f0;
    padding-top: 8px;
  }}
  .deleted-title {{
    font-size: 12px;
    color: #475569;
    margin-bottom: 6px;
    font-weight: 600;
  }}
  .deleted-list {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .deleted-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 8px;
    padding: 5px 6px;
  }}
  .deleted-text {{
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 12px;
    color: #7c2d12;
  }}
  .undo-delete-btn {{
    border: 0;
    background: #ea580c;
    color: #fff;
    font-size: 11px;
    border-radius: 6px;
    padding: 4px 7px;
    cursor: pointer;
    flex-shrink: 0;
  }}
  .deleted-empty {{
    font-size: 12px;
    color: #94a3b8;
    padding: 2px 0;
  }}
  .outline-delete {{
    border: 0;
    background: transparent;
    color: #94a3b8;
    width: 18px;
    height: 18px;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    pointer-events: none;
    transition: opacity 120ms ease, color 120ms ease, background 120ms ease;
    flex-shrink: 0;
  }}
  .outline-section-item:hover .outline-delete,
  .outline-entry-item:hover .outline-delete {{
    opacity: 1;
    pointer-events: auto;
  }}
  .outline-delete:hover {{
    color: #ef4444;
    background: #fee2e2;
  }}
  .save-wrap {{
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }}
  .save-wrap small {{
    color: #374151;
    font-size: 12px;
    text-align: center;
    line-height: 1.3;
    background: #f3f4f6;
    padding: 4px 8px;
    border-radius: 6px;
  }}
  .photo-upload-overlay {{
    position: absolute;
    inset: 0;
    border: 0;
    background: rgba(17, 24, 39, 0.26);
    color: #fff;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    opacity: 0;
    transition: opacity 120ms ease;
    cursor: pointer;
  }}
  .photo-upload-overlay .plus {{
    font-size: 22px;
    line-height: 1;
    font-weight: 700;
  }}
  .photo-upload-overlay .txt {{
    font-size: 11px;
  }}
  .photo-slot:hover .photo-upload-overlay,
  .profile-photo-circle:hover .photo-upload-overlay {{
    opacity: 1;
  }}
  .photo-upload-overlay.circle {{
    border-radius: 999px;
  }}
  .is-editing .editable-node {{
    outline: 1px dashed #60a5fa;
    outline-offset: 1px;
    background: rgba(191, 219, 254, 0.18);
  }}
  .print-modal-backdrop {{
    position: fixed;
    inset: 0;
    background: rgba(17, 24, 39, 0.35);
    z-index: 9998;
  }}
  .print-modal {{
    position: fixed;
    right: 190px;
    top: 20px;
    z-index: 9999;
    min-width: 260px;
    border-radius: 10px;
    padding: 10px 12px;
    background: #111827;
    color: #f9fafb;
    font-size: 12px;
    line-height: 1.4;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
  }}
  .print-tip-title {{
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .print-modal-actions {{
    margin-top: 8px;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }}
  .print-modal-actions button {{
    border: 0;
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 12px;
    cursor: pointer;
  }}
  .print-modal-actions .btn-secondary {{
    background: #e5e7eb;
    color: #111827;
  }}
  .print-modal-actions .btn-primary {{
    background: #2563eb;
    color: #fff;
  }}
  .hidden {{
    display: none;
  }}
  @media print {{
    .outline-panel,
    .editor-toolbar {{
      display: none !important;
    }}
    .print-modal,
    .print-modal-backdrop {{
      display: none !important;
    }}
    .editable-node {{
      outline: none !important;
      background: transparent !important;
    }}
  }}
</style>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render one-page resume HTML from JSON.")
    parser.add_argument("--input", required=True, help="Path to normalized resume JSON file")
    parser.add_argument("--output", default="", help="Path to output HTML file (optional; auto-named if omitted)")
    parser.add_argument(
        "--style",
        default="stripe",
        choices=["stripe", "compact", "sidebar", "classic", "modern", "minimal"],
        help="Layout style: stripe/compact/sidebar (classic/modern/minimal kept as aliases)",
    )
    parser.add_argument("--accent", default="", help="Accent color in hex, e.g. #1f4e8c")
    parser.add_argument("--sidebar-bg", default="", help="Sidebar background color in hex for sidebar style")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    style_name = STYLE_ALIASES.get(args.style, args.style)
    html_text = build_html(data, style_name, args.accent, args.sidebar_bg)
    output_path = Path(args.output).resolve() if args.output else default_output_path(args.input, style_name, data)
    output_path.write_text(html_text, encoding="utf-8")
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
