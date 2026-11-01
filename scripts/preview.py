#!/usr/bin/env python3
"""Build an explicit local media review package, or serve it on loopback."""
import argparse
import html
import json
import re
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


def esc(value):
    return html.escape(str(value), quote=True)


def build(manifest, out):
    source = Path(manifest).resolve()
    data = json.loads(source.read_text(encoding='utf-8'))
    for key in ('title', 'version', 'items'):
        if key not in data:
            raise ValueError('Missing manifest field: ' + key)
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('Output already exists; choose a new draft/version directory')
    checked, ids = [], set()
    for item in data['items']:
        ident, kind = item['id'], item['kind']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', ident) or ident in ids:
            raise ValueError('Invalid or duplicate item id: ' + ident)
        ids.add(ident)
        if kind not in ('image', 'video', 'audio', 'text', 'file'):
            raise ValueError('Unsupported kind: ' + kind)
        files = {}
        for key in ('path', 'poster'):
            if key not in item:
                if key == 'path':
                    raise ValueError('Missing path: ' + ident)
                continue
            p = (source.parent / item[key]).resolve()
            if not p.is_file():
                raise ValueError('Missing file: ' + str(p))
            files[key] = p
        content = files['path'].read_text(encoding='utf-8') if kind == 'text' else None
        checked.append((item, files, content))
    # Validate all inputs before creating a partial delivery.
    (out / 'media').mkdir(parents=True)
    sections, packed = [], []
    for item, files, content in checked:
        entry = dict(item)
        for key, p in files.items():
            rel = 'media/' + item['id'] + ('-poster' if key == 'poster' else '') + p.suffix.lower()
            shutil.copy2(p, out / rel)
            entry[key] = rel
        url, kind, ident = quote(entry['path']), item['kind'], item['id']
        title = esc(item.get('title', ident))
        media = ''
        if kind == 'image':
            media = f'<a href="{url}"><img src="{url}" alt="{title}" loading="lazy"></a>'
        elif kind in ('video', 'audio'):
            poster = f' poster="{quote(entry["poster"])}"' if 'poster' in entry and kind == 'video' else ''
            media = f'<{kind} controls preload="metadata" playsinline{poster} src="{url}"></{kind}><p class="load">等待媒体加载；也可使用下方文件链接。</p>'
        elif kind == 'text':
            media = f'<details open><summary>查看文本</summary><button class="copy" data-target="text-{ident}">复制全文</button><pre id="text-{ident}">{esc(content)}</pre></details>'
        sections.append(f'<section id="{ident}"><h2>{title}</h2><p>{esc(item.get("note", ""))}</p>{media}<a class="download" href="{url}" download>下载／打开文件</a></section>')
        packed.append(entry)
    changes = ''.join('<li>' + esc(x) + '</li>' for x in data.get('changes', []))
    limits = ''.join('<li>' + esc(x) + '</li>' for x in data.get('limitations', []))
    states = ''.join(f'<span><b>{esc(k)}</b>：{esc(v)}</span>' for k, v in data.get('statuses', {}).items())
    nav = ''.join(f'<a href="#{x[0]["id"]}">{esc(x[0].get("title", x[0]["id"]))}</a>' for x in checked)
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>''' + esc(data['title']) + '''</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:auto;max-width:1200px;padding:28px 20px 60px;background:#11191e;color:#eef3f5;font:17px/1.65 system-ui,sans-serif}h1{font-size:clamp(26px,4vw,42px);line-height:1.2}h2{font-size:23px}a{color:#97dfe8;overflow-wrap:anywhere}header,section{margin-bottom:24px}section{padding:24px;background:#1c272f;border:1px solid #35444e;border-radius:16px;scroll-margin-top:20px}img,video{display:block;width:100%;max-height:75vh;object-fit:contain;border-radius:8px;background:#080d10}audio{width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.8 system-ui;background:#10181e;padding:18px;border-radius:8px}button{font:inherit;cursor:pointer;padding:6px 14px;color:#eef3f5;background:#294450;border:1px solid #5b8797;border-radius:8px}button:focus-visible,a:focus-visible{outline:3px solid #ffda86}.states,nav{display:flex;flex-wrap:wrap;gap:12px}.states span{background:#24343e;padding:7px 12px;border-radius:8px}nav{margin:22px 0}p,.load{color:#c1cdd3}.download{display:inline-block;margin-top:12px}.load.error{color:#ffb4a9}footer{color:#a3b4bd;font-size:14px}@media(max-width:600px){body{padding:20px 12px}section{padding:16px}}
</style></head><body><header><p>''' + esc(data['version']) + '</p><h1>' + esc(data['title']) + '</h1><div class="states">' + states + '</div><ul>' + changes + '</ul><ul>' + limits + '</ul><nav>' + nav + '</nav></header>' + ''.join(sections) + '''<footer>本地预览页。素材已生成不等于最终成片已验收；Canvas 状态以上方实际记录为准。</footer><script>
for (const media of document.querySelectorAll('video,audio')) {
 const status=media.nextElementSibling;
 media.addEventListener('loadedmetadata',()=>{status.textContent='媒体已加载 · '+media.duration.toFixed(2)+' 秒（请播放并检查内容）';});
 media.addEventListener('error',()=>{status.classList.add('error');status.textContent='媒体加载失败。请检查 HTTP 服务、文件路径和编码，或下载原文件。';});
}
for (const img of document.images) img.addEventListener('error',()=>{const p=document.createElement('p');p.textContent='图片加载失败，请检查文件路径。';img.after(p);});
for (const button of document.querySelectorAll('.copy')) button.addEventListener('click',async()=>{
 const text=document.getElementById(button.dataset.target).textContent;
 try {await navigator.clipboard.writeText(text);button.textContent='已复制';} catch {button.textContent='请在下方手动选择复制';}
});
</script></body></html>'''
    (out / 'index.html').write_text(page, encoding='utf-8')
    data['items'] = packed
    (out / 'preview-manifest.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(out / 'index.html')


class PreviewHandler(SimpleHTTPRequestHandler):
    """Single-byte-range streaming with HEAD support and no directory listings."""
    def list_directory(self, path):
        self.send_error(403, 'Directory listing disabled')
        return None

    def send_head(self):
        self.byte_range = None
        root = Path(self.directory).resolve()
        p = Path(self.translate_path(self.path)).resolve()
        if not p.is_relative_to(root):
            self.send_error(403)
            return None
        if p.is_dir():
            p = (p / 'index.html').resolve()
        if not p.is_relative_to(root):
            self.send_error(403)
            return None
        if not p.is_file():
            self.send_error(404)
            return None
        f = p.open('rb')
        size = p.stat().st_size
        start, end = 0, size - 1
        requested = self.headers.get('Range')
        if requested:
            m = re.fullmatch(r'bytes=(\d*)-(\d*)', requested.strip())
            if m and size and (m[1] or m[2]):
                if m[1]:
                    start = int(m[1]); end = min(int(m[2]), size-1) if m[2] else size-1
                else:
                    length = int(m[2]); start = max(0, size-length)
                valid = 0 <= start <= end < size
            else:
                valid = False
            if not valid:
                f.close(); self.send_response(416); self.send_header('Content-Range', f'bytes */{size}'); self.send_header('Content-Length','0'); self.end_headers(); return None
            self.byte_range = (start, end)
        self.send_response(206 if requested else 200)
        self.send_header('Content-Type', self.guess_type(str(p)))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end-start+1))
        self.send_header('Cache-Control', 'no-cache')
        if requested:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        return f

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        start, end = self.byte_range
        source.seek(start); remaining = end-start+1
        try:
            while remaining:
                chunk = source.read(min(65536, remaining))
                if not chunk: break
                outputfile.write(chunk); remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build'); b.add_argument('manifest'); b.add_argument('--out', required=True)
    s = sub.add_parser('serve'); s.add_argument('root'); s.add_argument('--port', type=int, default=8768)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.manifest, args.out)
    else:
        root = Path(args.root).resolve()
        if not root.is_dir(): parser.error('Preview root must be an existing directory')
        server = ThreadingHTTPServer(('127.0.0.1',args.port), partial(PreviewHandler,directory=str(root)))
        print(f'Preview root: {root}\nURL: http://127.0.0.1:{server.server_port}/', flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()

if __name__ == '__main__':
    main()
