# -*- coding: utf-8 -*-
"""Build DASE7501_Focus_Interactive.html from DASE7501_Focus_Paper_L1L2L4.md."""
import re, html, io, os, base64

SRC = 'DASE7501_Focus_Paper_L1L2L4.md'
OUT = 'DASE7501_Focus_Interactive.html'
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'katex_assets')

KEY = {1:'D',2:'C',3:'B',4:'C',5:'C',6:'C',7:'C',8:'B',9:'B',10:'A',
       11:'F',12:'T',13:'T',14:'T'}
WARNINGS = []

def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

def katex_css_inline():
    css = read(os.path.join(ASSET_DIR, 'katex.min.css'))
    cache = {}
    def repl(m):
        name = m.group(1)
        if name not in cache:
            cache[name] = base64.b64encode(open(os.path.join(ASSET_DIR, 'fonts', name), 'rb').read()).decode('ascii')
        return 'url(data:font/woff2;base64,%s)' % cache[name]
    return re.sub(r'url\(fonts/([A-Za-z0-9_.-]+\.woff2)\)[^;}]*', repl, css)

def strip_frontmatter(lines):
    if lines and lines[0].strip() == '---':
        for i, l in enumerate(lines[1:], 1):
            if l.strip() == '---':
                return lines[i+1:]
    return lines

# ---------------- math / inline / blocks (same as build_site.py) ----------------

MATH_TOKENS = []

def pre_math(s):
    s = s.replace('°', '\\degree ').replace('×', '\\times ').replace('−', '-')
    s = re.sub(r'^\^', '{}^', s)
    s = re.sub(r'(?<=[\s=(<])\^', '{}^', s)
    s = re.sub(r'^\_(?=[A-Za-z{])', '{}_', s)
    s = re.sub(r'(?<=[\s=(<])_(?=[A-Za-z{])', '{}_', s)
    s = re.sub(r'√\{([^}]*)\}', r'\\sqrt{\1}', s)
    s = re.sub(r'√([A-Za-z0-9])', r'\\sqrt{\1}', s)
    return s

def math_token(m):
    s = m.group(0)
    disp = s.startswith('$$')
    inner = s[2:-2] if disp else s[1:-1]
    inner = pre_math(inner)
    tok = ('<div class="mb">$$%s$$</div>' % inner) if disp else ('<span class="mi">$%s$</span>' % inner)
    MATH_TOKENS.append(tok)
    return '\x00M%d\x00' % (len(MATH_TOKENS)-1)

def stash_math(text):
    text = re.sub(r'\$\$([^$]+?)\$\$', math_token, text)
    text = re.sub(r'\$([^$\n]+?)\$', math_token, text)
    return text

def restore_math(text):
    return re.sub(r'\x00M(\d+)\x00', lambda m: MATH_TOKENS[int(m.group(1))], text)

def inline(text):
    text = stash_math(text)
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', text)
    return restore_math(text)

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

# ---------------- parse the focus paper ----------------

def parse_paper(text):
    lines = strip_frontmatter(text.split('\n'))
    idx2 = next(i for i, l in enumerate(lines) if l.strip().startswith('# Part 2'))
    part1, part2 = lines[:idx2], '\n'.join(lines[idx2:])

    # part 1 -> sections
    secs = {}
    cur = None
    for l in part1:
        m = re.match(r'^## Section ([A-D]): (.+)$', l.strip())
        if m:
            cur = m.group(1)
            secs[cur] = {'title': m.group(2), 'intro': [], 'lines': []}
            continue
        if not cur:
            continue
        if l.strip().startswith('# '):
            cur = None
            continue
        secs[cur]['lines'].append(l)

    qs = {}
    for sec, d in secs.items():
        intro, qblocks = [], []
        curq = None
        for l in d['lines']:
            m = re.match(r'^\*\*Q(\d+)\.\*\*\s?(.*)$', l.strip())
            if m:
                if curq is not None:
                    qblocks.append(curq)
                curq = {'n': int(m.group(1)), 'text': [m.group(2)]}
            elif curq is not None:
                if l.strip():
                    curq['text'].append(l.strip())
            else:
                if l.strip():
                    intro.append(l.strip())
        if curq is not None:
            qblocks.append(curq)
        d['intro'] = intro
        for qb in qblocks:
            n = qb['n']
            txt = list(qb['text'])
            opts = []
            if n <= 10:
                while txt and not re.match(r'^[A-D]\.\s', txt[-1].strip()):
                    txt.pop()
                while txt and re.match(r'^[A-D]\.\s', txt[-1].strip()):
                    opts.insert(0, txt.pop())
                if len(opts) != 4:
                    WARNINGS.append('Q%d: expected 4 options, got %d' % (n, len(opts)))
            qs[n] = {'n': n, 'sec': sec, 'text': txt, 'opts': opts}
        if len(qblocks) != {'A': 10, 'B': 4, 'C': 4, 'D': 2}[sec]:
            WARNINGS.append('Section %s: expected %d questions, got %d'
                            % (sec, {'A': 10, 'B': 4, 'C': 4, 'D': 2}[sec], len(qblocks)))

    # part 2 -> solutions
    sol = {}
    for m in re.finditer(r'^\*\*Q(\d+)\. [A-DTF]\.\*\*\s*(.*)$', part2, re.M):
        sol[int(m.group(1))] = m.group(2).strip()
    for m in re.finditer(r'^> \*\*【Q(\d+) 详解】\*\*$', part2, re.M):
        n = int(m.group(1))
        rest = part2[m.end():]
        nxt = re.search(r'^> \*\*【Q\d+ 详解】\*\*$', rest, re.M)
        chunk = rest if not nxt else rest[:nxt.start()]
        body = []
        for ln in chunk.split('\n'):
            s = ln.strip()
            if s.startswith('>'):
                body.append(s[1:].lstrip(' '))
            elif s:
                break
        sol[n] = body
    qkm = re.search(r'^\*\*Quick key \(速查\)\*\*:\s*(.*)$', part2, re.M)
    return secs, qs, sol, (qkm.group(1).strip() if qkm else '')

# ---------------- render ----------------

def render_q(n, q, sol):
    typ = 'mcq' if n <= 10 else ('tf' if n <= 14 else 'reveal')
    tag_zh = {'mcq': '选择题', 'tf': '判断题', 'reveal': '计算题' if n <= 18 else '简答题'}[typ]
    ans = KEY.get(n, '')
    parts = ['<div class="q" data-sec="%s" data-id="q%d" data-type="%s" data-answer="%s">'
             % (q['sec'], n, typ, ans)]
    parts.append('<div class="q-top"><span class="tag tag-%s">%s</span>'
                 '<span class="qnum">Q%d</span></div>' % (typ if typ != 'reveal' else 'reveal', tag_zh, n))
    parts.append('<div class="qtext">%s</div>' % blocks('\n'.join(q['text'])))
    if typ == 'mcq':
        parts.append('<div class="opts">')
        for line in q['opts']:
            m = re.match(r'^([A-D])\.\s(.*)$', line)
            letter, txt = m.group(1), m.group(2)
            parts.append('<button class="opt" data-opt="%s"><span class="ol">%s</span>'
                         '<span class="ot">%s</span></button>' % (letter, letter, inline(txt)))
        parts.append('</div>')
    if typ == 'tf':
        parts.append('<div class="opts tf"><button class="opt" data-opt="T"><span class="ol">T</span>'
                     '<span class="ot">True (正确)</span></button>'
                     '<button class="opt" data-opt="F"><span class="ol">F</span>'
                     '<span class="ot">False (错误)</span></button></div>')
    if typ == 'reveal':
        parts.append('<button class="rev-btn">点击显示答案解析 ▾</button>')
    parts.append('<div class="sol hidden">')
    if typ in ('mcq', 'tf'):
        ans_txt = ans if typ == 'mcq' else ('True (正确)' if ans == 'T' else 'False (错误)')
        parts.append('<div class="sol-tag">正确答案:%s</div>' % ans_txt)
    parts.append('<div class="sol-body">%s</div></div></div>'
                 % blocks('\n'.join(sol) if isinstance(sol, list) else sol))
    return '\n'.join(parts)

# ---------------- CSS / JS (same style as build_site.py) ----------------

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

JS = r'''
(function(){
  var LS='dase7501_focus_v1';
  var state={};
  try{ state=JSON.parse(localStorage.getItem(LS))||{}; }catch(e){ state={}; }
  function save(){ try{ localStorage.setItem(LS, JSON.stringify(state)); }catch(e){} }
  function showSol(q){ q.querySelector('.sol').classList.remove('hidden'); }
  function hideSol(q){ q.querySelector('.sol').classList.add('hidden'); }
  function lockAndMark(q, choice, ok){
    q.dataset.locked='1';
    var ans=q.dataset.answer;
    q.querySelectorAll('.opt').forEach(function(o){
      o.disabled=true;
      if(o.dataset.opt===ans) o.classList.add('correct');
    });
    var chosen=q.querySelector('.opt[data-opt="'+choice+'"]');
    if(ok){ chosen.classList.add('correct'); } else { chosen.classList.add('wrong'); }
    showSol(q);
  }
  function unlock(q){
    delete q.dataset.locked;
    q.querySelectorAll('.opt').forEach(function(o){
      o.disabled=false; o.classList.remove('correct','wrong');
    });
    hideSol(q);
    var b=q.querySelector('.rev-btn'); if(b) b.textContent='点击显示答案解析 ▾';
  }
  var SECS=[['A','Section A · Multiple Choice'],['B','Section B · True/False'],
             ['C','Section C · Calculation'],['D','Section D · Short Answer']];
  function updateAll(){
    var grand={t:0,d:0,c:0};
    var rows=[];
    SECS.forEach(function(se){
      var sid=se[0]; var t=0,d=0,c=0;
      document.querySelectorAll('.q[data-sec="'+sid+'"]').forEach(function(q){
        t++;
        var st=state[q.dataset.id];
        if(q.dataset.type==='reveal'){ if(st&&st.r) d++; }
        else if(st&&st.c!==undefined){ d++; if(st.ok) c++; }
      });
      grand.t+=t; grand.d+=d; grand.c+=c;
      rows.push({name:se[1], t:t, d:d, c:c, acc:d?Math.round(100*c/d):0});
    });
    var p=grand.t?Math.round(100*grand.d/grand.t):0;
    document.getElementById('head-progress').textContent='进度 '+grand.d+'/'+grand.t+' ('+p+'%)';
    document.getElementById('head-bar').querySelector('i').style.width=p+'%';
    var fs=document.getElementById('final-stats');
    var h='<h3>成绩单 · Report Card</h3>';
    rows.forEach(function(r){
      var p=r.t?Math.round(100*r.d/r.t):0;
      h+='<div class="fs-row"><span style="min-width:200px">'+r.name+'</span>'+
         '<span class="bar"><i style="width:'+p+'%"></i></span>'+
         '<span style="min-width:150px;text-align:right">'+r.d+'/'+r.t+' 题 · 答对 '+r.c+' · 正确率 '+r.acc+'%</span></div>';
    });
    var tp=grand.t?Math.round(100*grand.d/grand.t):0;
    h+='<div class="fs-row"><strong>总计</strong><span class="bar"><i style="width:'+tp+'%"></i></span>'+
       '<span style="min-width:150px;text-align:right"><strong>'+grand.d+'/'+grand.t+' ('+tp+'%)</strong></span></div>';
    fs.innerHTML=h;
  }
  document.querySelectorAll('.q[data-type="mcq"] .opt, .q[data-type="tf"] .opt').forEach(function(btn){
    btn.addEventListener('click', function(){
      var q=btn.closest('.q'); if(q.dataset.locked) return;
      var ok=(btn.dataset.opt===q.dataset.answer);
      state[q.dataset.id]={c:btn.dataset.opt, ok:ok};
      save(); lockAndMark(q, btn.dataset.opt, ok); updateAll();
    });
  });
  document.querySelectorAll('.q[data-type="reveal"] .rev-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      var q=btn.closest('.q'); var sol=q.querySelector('.sol');
      if(sol.classList.contains('hidden')){ showSol(q); btn.textContent='收起答案解析 ▴'; state[q.dataset.id]={r:true}; }
      else { hideSol(q); btn.textContent='点击显示答案解析 ▾'; delete state[q.dataset.id]; }
      save(); updateAll();
    });
  });
  document.querySelectorAll('.reset').forEach(function(b){
    b.addEventListener('click', function(){
      document.querySelectorAll('.q').forEach(function(q){
        delete state[q.dataset.id]; unlock(q);
      });
      save(); updateAll();
    });
  });
  Object.keys(state).forEach(function(id){
    var q=document.querySelector('.q[data-id="'+id+'"]'); if(!q) return;
    var st=state[id];
    if(q.dataset.type==='reveal'){ if(st.r){ showSol(q); q.querySelector('.rev-btn').textContent='收起答案解析 ▴'; } }
    else if(st.c!==undefined){ lockAndMark(q, st.c, !!st.ok); }
  });
  updateAll();
  var tb=document.getElementById('theme-btn');
  if(tb){ tb.addEventListener('click', function(){
    var cur=document.documentElement.dataset.theme||'auto';
    var nxt=cur==='auto'?'light':(cur==='light'?'dark':'auto');
    if(nxt==='auto') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme=nxt;
    tb.textContent='主题:'+(nxt==='auto'?'自动':(nxt==='light'?'浅色':'深色'));
  }); }
  function selfcheck(){
    var sc=document.getElementById('selfcheck'); if(!sc) return;
    var missing=[];
    document.querySelectorAll('.q').forEach(function(q){
      if(q.dataset.type!=='reveal' && !q.dataset.answer) missing.push(q.dataset.id);
    });
    sc.textContent=JSON.stringify({
      questions:document.querySelectorAll('.q').length,
      mcq:document.querySelectorAll('.q[data-type="mcq"]').length,
      tf:document.querySelectorAll('.q[data-type="tf"]').length,
      reveal:document.querySelectorAll('.q[data-type="reveal"]').length,
      katexLoaded:!!window.katex,
      katexNodes:document.querySelectorAll('.katex').length,
      katexErrors:document.querySelectorAll('.katex-error').length,
      missingAnswers:missing
    });
  }
  window.addEventListener('load', function(){ setTimeout(selfcheck, 2000); });
})();
'''

def main():
    text = read(SRC)
    secs, qs, sol, quick_key = parse_paper(text)

    body = []
    body.append('<header class="hero"><div class="hero-inner">'
                '<div><h1>DASE7501 聚焦卷互动版 · Focus Paper (L1 · L2 · L4)</h1>'
                '<div class="sub">20 题 · 100 分 · 建议 60 分钟 · 选择题/判断题点击作答,计算题/简答题点击显示解析</div></div>'
                '<button id="theme-btn">主题:自动</button>'
                '<div class="prog"><span class="lbl" id="head-progress">进度 0/20</span>'
                '<div class="bar" id="head-bar"><i></i></div></div></div></header>')
    body.append('<main><section class="chapter" id="focus" data-ch="focus">')
    body.append('<h2 class="ch-title">Focus Paper <span class="ch-en">Lectures 1, 2 &amp; 4 · modelled on HW1 and past-exam styles</span></h2>')
    body.append('<div class="callout">本卷题目与真实考试一致为<strong>纯英文</strong>;作答后自动判分并展开中文解析,可随时点击「主题」切换深浅色。</div>')

    order = ['A', 'B', 'C', 'D']
    for sec in order:
        d = secs[sec]
        body.append('<h3 class="grp">%s</h3>' % html.escape(d['title']))
        if d['intro']:
            body.append(blocks('\n'.join(d['intro'])))
        for n in sorted(q for q in qs if qs[q]['sec'] == sec):
            body.append(render_q(n, qs[n], sol.get(n, '')))

    body.append('<h3 class="grp">答案速查 · Quick Key(考后对照)</h3>')
    body.append('<details class="panel"><summary>展开 Quick Key 速查表</summary>'
                '<div class="panel-body"><p>%s</p></div></details>' % inline(quick_key))

    body.append('<div class="final-stats" id="final-stats"></div>')
    body.append('<button class="reset">重置全部作答</button>')
    body.append('</section></main>')
    body.append('<div id="selfcheck" style="display:none"></div>')

    html_doc = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n'
                '<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                '<title>DASE7501 聚焦卷互动 · Focus Paper L1 L2 L4</title>\n'
                '<meta name="description" content="DASE7501 聚焦卷(Lecture 1/2/4)互动练习:20 题,点击作答自动判分">\n'
                '<style>%s</style>\n'
                '<style>%s</style>\n</head>\n<body>\n%s\n'
                '<script>%s</script>\n'
                '<script>%s</script>\n'
                '<script>%s</script>\n'
                '<script>document.addEventListener("DOMContentLoaded",function(){'
                'if(window.renderMathInElement){renderMathInElement(document.body,'
                '{delimiters:[{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}],'
                'throwOnError:false});}});</script>\n'
                '</body>\n</html>\n') % (katex_css_inline(), CSS, '\n'.join(body),
                                        read(os.path.join(ASSET_DIR, 'katex.min.js')),
                                        read(os.path.join(ASSET_DIR, 'auto-render.min.js')), JS)

    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print('questions:', len(qs))
    print('solutions:', sorted(sol))
    print('warnings:', WARNINGS or 'none')
    print('written:', OUT)

if __name__ == '__main__':
    main()
