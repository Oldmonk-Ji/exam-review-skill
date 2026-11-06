"""Course-neutral offline Markdown/math rendering and visual styles."""
import re, html, io, os, base64

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'katex_assets')

def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

def katex_css_inline():
    css = read(os.path.join(ASSET_DIR, 'katex.min.css'))
    def repl(m):
        name = m.group(1)
        with open(os.path.join(ASSET_DIR, 'fonts', name), 'rb') as font:
            encoded = base64.b64encode(font.read()).decode('ascii')
        mime = {'woff2':'font/woff2', 'woff':'font/woff', 'ttf':'font/ttf'}[name.rsplit('.', 1)[1]]
        return 'url(data:%s;base64,%s)' % (mime, encoded)
    return re.sub(r'url\(fonts/([A-Za-z0-9_.-]+\.woff2)\)[^;}]*', repl, css)

# ---------------- math / inline / blocks (same as build_site.py) ----------------

def pre_math(s):
    s = s.replace('°', '\\degree ').replace('×', '\\times ').replace('−', '-')
    s = re.sub(r'^\^', '{}^', s)
    s = re.sub(r'(?<=[\s=(<])\^', '{}^', s)
    s = re.sub(r'^\_(?=[A-Za-z{])', '{}_', s)
    s = re.sub(r'(?<=[\s=(<])_(?=[A-Za-z{])', '{}_', s)
    s = re.sub(r'√\{([^}]*)\}', r'\\sqrt{\1}', s)
    s = re.sub(r'√([A-Za-z0-9])', r'\\sqrt{\1}', s)
    return s

def inline(text):
    tokens = []
    def token(m):
        value = m.group(0)
        display = value.startswith('$$')
        inner = html.escape(pre_math(value[2:-2] if display else value[1:-1]))
        tokens.append(('<span class="mb">$$%s$$</span>' if display else '<span class="mi">$%s$</span>') % inner)
        return '\x00M%d\x00' % (len(tokens)-1)
    text = text.replace('\x00', '')
    text = re.sub(r'\$\$[^$]+?\$\$|\$[^$\n]+?\$', token, text)
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'\[([^\]\n]+)\]\((https?://[^\s)]+)\)', r'<a href="\2">\1</a>', text)
    return re.sub(r'\x00M(\d+)\x00', lambda m: tokens[int(m.group(1))], text)


def render_table(tbl):
    rows = [[c.strip() for c in r.strip('|').split('|')] for r in tbl]
    rows = [r for r in rows if not all(re.fullmatch(r'[-: ]+', c or '-') for c in r)]
    out = ['<div class="tbl-wrap"><table>']
    for ri, r in enumerate(rows):
        tag = 'th' if ri == 0 else 'td'
        out.append('<tr>' + ''.join('<%s>%s</%s>' % (tag, inline(c), tag) for c in r) + '</tr>')
    out.append('</table></div>')
    return ''.join(out)

def blocks(text):
    lines = text.split('\n')
    out = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith('|'):
            tbl = []
            while i < n and lines[i].strip().startswith('|'):
                tbl.append(lines[i].strip()); i += 1
            out.append(render_table(tbl))
            continue
        if re.match(r'^\d+\.\s', s):
            items = []
            while i < n and lines[i].strip() and re.match(r'^\d+\.\s', lines[i].strip()):
                items.append('<li>%s</li>' % inline(re.sub(r'^\d+\.\s', '', lines[i].strip())))
                i += 1
            out.append('<ol>%s</ol>' % ''.join(items))
            continue
        if s.startswith('- ') and not s.startswith('---'):
            items = []
            while i < n and lines[i].strip().startswith('- '):
                items.append('<li>%s</li>' % inline(lines[i].strip()[2:]))
                i += 1
            out.append('<ul>%s</ul>' % ''.join(items))
            continue
        if s.startswith('>'):
            q = []
            while i < n and lines[i].strip().startswith('>'):
                q.append(lines[i].strip()[1:].lstrip(' '))
                i += 1
            out.append('<div class="callout">%s</div>' % blocks('\n'.join(q)))
            continue
        par = [s]
        i += 1
        while (i < n and lines[i].strip() and
               not lines[i].strip().startswith(('|', '>')) and
               not re.match(r'^\d+\.\s', lines[i].strip()) and
               not lines[i].strip().startswith('- ')):
            par.append(lines[i].strip())
            i += 1
        out.append('<p>%s</p>' % inline(' '.join(par)))
    return '\n'.join(out)

CSS = r'''
:root{
  --bg:#eef2f9; --card:#ffffff; --text:#1d2637; --muted:#5f6d88;
  --line:#d9e1f0; --accent:#3f6dff; --accent2:#8a5cf6;
  --good:#178a56; --goodbg:#e5f6ec; --bad:#d64550; --badbg:#fdecee;
  --panel:#f4f7ff; --head-g1:#3f6dff; --head-g2:#8a5cf6;
  --tag-mcq:#3f6dff; --tag-tf:#8a5cf6; --tag-calc:#0e9c96;
  --shadow:0 2px 10px rgba(30,45,90,.08);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0d1220; --card:#161e31; --text:#e6ecf8; --muted:#93a1bd;
    --line:#283450; --accent:#6b93ff; --accent2:#a689ff;
    --good:#43c58b; --goodbg:#12301f; --bad:#ff7484; --badbg:#3a1620;
    --panel:#1a2440; --head-g1:#2f56d8; --head-g2:#6d43d0;
    --shadow:0 2px 12px rgba(0,0,0,.4);
  }
}
:root[data-theme="dark"]{
  --bg:#0d1220; --card:#161e31; --text:#e6ecf8; --muted:#93a1bd;
  --line:#283450; --accent:#6b93ff; --accent2:#a689ff;
  --good:#43c58b; --goodbg:#12301f; --bad:#ff7484; --badbg:#3a1620;
  --panel:#1a2440; --head-g1:#2f56d8; --head-g2:#6d43d0;
  --shadow:0 2px 12px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:"Segoe UI","Microsoft YaHei","PingFang SC",system-ui,sans-serif;
  font-size:15.5px;line-height:1.65}
.wrap{max-width:960px;margin:0 auto;padding:0 16px}
header.hero{background:linear-gradient(120deg,var(--head-g1),var(--head-g2));
  color:#fff;padding:22px 16px;position:sticky;top:0;z-index:50;
  box-shadow:0 4px 18px rgba(30,45,90,.25)}
.hero-inner{max-width:960px;margin:0 auto;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.hero h1{margin:0;font-size:20px;letter-spacing:.5px}
.hero .sub{font-size:12.5px;opacity:.85;margin-top:2px}
.hero .prog{margin-left:auto;display:flex;flex-direction:column;gap:4px;min-width:220px}
.hero .prog .lbl{font-size:12.5px;text-align:right}
.bar{height:8px;background:rgba(255,255,255,.25);border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;width:0;background:#fff;border-radius:99px;transition:width .4s ease}
#theme-btn{margin-left:auto;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.4);
  color:#fff;border-radius:99px;padding:5px 14px;font-size:12.5px;cursor:pointer}
#theme-btn:hover{background:rgba(255,255,255,.28)}
main{max-width:960px;margin:0 auto;padding:18px 16px 60px}
.chapter{background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:22px 24px;margin-bottom:22px;box-shadow:var(--shadow)}
.ch-title{font-size:21px;margin:0 0 2px;background:linear-gradient(100deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.ch-en{font-size:13px;color:var(--muted);font-weight:400;-webkit-text-fill-color:var(--muted)}
.grp{margin:22px 0 8px;font-size:15.5px;color:var(--accent);border-left:4px solid var(--accent);
  padding-left:10px}
details.panel{border:1px solid var(--line);border-radius:11px;margin-bottom:9px;background:var(--panel);overflow:hidden}
details.panel summary{cursor:pointer;padding:10px 14px;font-weight:600;font-size:14.5px;list-style:none;
  display:flex;align-items:center;gap:8px}
details.panel summary::-webkit-details-marker{display:none}
details.panel summary::before{content:'▸';color:var(--accent);transition:transform .2s;font-size:13px}
details.panel[open] summary::before{transform:rotate(90deg)}
details.panel .panel-body{padding:4px 16px 12px;border-top:1px dashed var(--line)}
.callout{background:var(--panel);border-left:4px solid var(--accent2);border-radius:8px;
  padding:8px 14px;margin:10px 0}
.tbl-wrap{overflow-x:auto;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{background:var(--panel);color:var(--accent)}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
tr:nth-child(even) td{background:color-mix(in srgb, var(--panel) 45%, transparent)}
.q{border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0;background:var(--card)}
.q-top{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.tag{font-size:11.5px;font-weight:700;color:#fff;border-radius:99px;padding:2px 11px;letter-spacing:.5px}
.tag-mcq{background:var(--tag-mcq)} .tag-tf{background:var(--tag-tf)} .tag-reveal{background:var(--tag-calc)}
.qnum{font-weight:700;color:var(--muted);font-size:13.5px}
.qtext p{margin:6px 0}
.opts{display:flex;flex-direction:column;gap:7px;margin:10px 0 4px}
.opts.tf{flex-direction:row;flex-wrap:wrap}
.opt{display:flex;align-items:flex-start;gap:10px;text-align:left;width:100%;cursor:pointer;
  background:var(--card);border:1.5px solid var(--line);border-radius:10px;padding:8px 12px;
  font:inherit;color:var(--text);transition:border-color .15s,transform .15s,background .15s}
.opts.tf .opt{width:auto;min-width:150px}
.opt:hover:not(:disabled){border-color:var(--accent);transform:translateY(-1px);background:var(--panel)}
.opt:disabled{cursor:default;opacity:.92}
.opt .ol{flex:none;width:22px;height:22px;border-radius:50%;background:var(--panel);border:1.5px solid var(--line);
  display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px}
.opt.correct{border-color:var(--good);background:var(--goodbg);animation:pop .3s ease}
.opt.correct .ol{background:var(--good);border-color:var(--good);color:#fff}
.opt.wrong{border-color:var(--bad);background:var(--badbg);animation:shake .35s ease}
.opt.wrong .ol{background:var(--bad);border-color:var(--bad);color:#fff}
@keyframes pop{50%{transform:scale(1.02)}}
@keyframes shake{25%{transform:translateX(-4px)}50%{transform:translateX(4px)}75%{transform:translateX(-2px)}}
.rev-btn{background:var(--panel);border:1.5px dashed var(--accent);color:var(--accent);font-weight:600;
  border-radius:9px;padding:7px 16px;cursor:pointer;font:inherit;font-size:13.5px;margin:8px 0 2px}
.rev-btn:hover{background:var(--accent);color:#fff}
.sol{border-left:4px solid var(--good);background:var(--goodbg);border-radius:0 10px 10px 0;
  padding:10px 14px;margin-top:10px;animation:slide .3s ease}
.sol.hidden{display:none}
@keyframes slide{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.sol-tag{font-weight:700;color:var(--good);font-size:13px;margin-bottom:4px}
.sol-body p{margin:6px 0}
.sol-body table{background:var(--card)}
.sol-body .callout{background:var(--card)}
.mb{margin:10px 0;overflow-x:auto}
.mi{white-space:nowrap}
.final-stats{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 24px;
  box-shadow:var(--shadow);margin-bottom:22px}
.final-stats h3{margin:0 0 10px;color:var(--accent)}
.fs-row{display:flex;justify-content:space-between;gap:14px;font-size:13.5px;padding:5px 0;
  border-bottom:1px dashed var(--line)}
.fs-row .bar{flex:1;background:var(--line);height:7px;align-self:center}
.fs-row .bar i{background:linear-gradient(90deg,var(--accent),var(--accent2))}
.reset{margin-top:10px;background:none;border:1px solid var(--line);color:var(--muted);
  border-radius:8px;padding:5px 14px;cursor:pointer;font:inherit;font-size:12.5px}
.reset:hover{border-color:var(--bad);color:var(--bad)}
@media (max-width:900px){
  .hero .prog{min-width:150px}
  .chapter{padding:16px 14px}
}
'''

