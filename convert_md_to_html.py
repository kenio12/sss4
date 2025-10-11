#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML converter for 同タイトル機能_改修計画書.md
"""

import re

def convert_markdown_to_html(md_file_path, html_file_path):
    """Convert markdown file to HTML with proper styling"""
    
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Start HTML
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>同タイトル機能改修計画書（案A）</title>
    <style>
        body {
            font-family: 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.8;
        }
        h1 {
            font-size: 2.2em;
            color: #1a1a1a;
            border-bottom: 3px solid #ff6b6b;
            padding-bottom: 10px;
            margin-top: 40px;
        }
        h2 {
            font-size: 1.8em;
            color: #2c3e50;
            margin-top: 30px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            font-size: 1.4em;
            color: #34495e;
            margin-top: 20px;
        }
        .separator {
            border-top: 2px solid #e74c3c;
            margin: 30px 0;
        }
        .metadata {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: bold;
        }
        code {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            display: block;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            margin: 20px 0;
            white-space: pre;
        }
        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        li {
            margin: 10px 0;
        }
        strong {
            color: #e74c3c;
            font-weight: bold;
        }
        .fire {
            color: #ff6b6b;
            font-weight: bold;
        }
        .arrow {
            color: #3498db;
            font-weight: bold;
            margin-left: 10px;
        }
        .checkbox {
            color: #27ae60;
        }
    </style>
</head>
<body>
"""
    
    # Process content line by line
    in_code_block = False
    code_content = []
    
    for line in md_content.split('\n'):
        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                # End code block
                html += '<code>' + '\n'.join(code_content) + '</code>\n'
                code_content = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            continue
        
        if in_code_block:
            code_content.append(line)
            continue
        
        # Headers
        if line.startswith('# '):
            html += f'<h1>{line[2:]}</h1>\n'
        elif line.startswith('## '):
            html += f'<h2>{line[3:]}</h2>\n'
        elif line.startswith('### '):
            html += f'<h3>{line[4:]}</h3>\n'
        # Separator
        elif line.startswith('━━━━━'):
            html += '<div class="separator"></div>\n'
        # Metadata
        elif line.startswith('**作成日**:') or line.startswith('**改修方針**:'):
            html += f'<div class="metadata">{line}</div>\n'
        # Lists
        elif line.startswith('- '):
            html += f'<ul><li>{line[2:]}</li></ul>\n'
        # <br> tags
        elif line.strip() == '<br>':
            html += '<br>\n'
        # Empty lines
        elif not line.strip():
            html += '<br>\n'
        # Regular paragraphs
        else:
            # Bold text
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            # Fire emoji emphasis
            line = re.sub(r'🔥🔥🔥', r'<span class="fire">🔥🔥🔥</span>', line)
            # Arrows
            line = re.sub(r'→', r'<span class="arrow">→</span>', line)
            # Checkboxes
            line = re.sub(r'✅', r'<span class="checkbox">✅</span>', line)
            html += f'<p>{line}</p>\n'
    
    # Close HTML
    html += """
</body>
</html>
"""
    
    # Write HTML file
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML変換完了: {html_file_path}")

if __name__ == '__main__':
    md_file = '/Users/keikeikun2/ai-try-programing/novel_site/同タイトル機能_改修計画書.md'
    html_file = '/Users/keikeikun2/ai-try-programing/novel_site/同タイトル機能_改修計画書.html'
    
    convert_markdown_to_html(md_file, html_file)
