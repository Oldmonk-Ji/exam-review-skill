"""Build a course-neutral single-file review using the upstream offline renderer."""
import hashlib
import html
import json
import re
import base64
import argparse
from schema import validate
from pathlib import Path
import review_base as base


def render_question(q):
    typ = q['type']
    attr = html.escape
    out = ['<div class="q" data-id="%s" data-sec="%s" data-type="%s" data-answer="%s">' %
           (attr(q['id']), attr(q['chapter']), typ, attr(q.get('answer', '')))]
    label = {'mcq': '选择题', 'tf': '判断题', 'reveal': '计算 / 简答'}[typ]
    out += ['<div class="q-top"><span class="tag">%s</span><strong>%s</strong><span>%s · %s · %s分</span><button class="bookmark">收藏 / 待重做</button></div>' %
            (label, attr(q['id']), attr(q.get('difficulty','')), attr(q.get('family','')), q.get('points',1)), '<div class="qtext">%s</div>' % base.blocks(q['text'])]
    options = q.get('options', {}) if typ == 'mcq' else ({'T': 'True', 'F': 'False'} if typ == 'tf' else {})
    if options:
        out.append('<div class="opts">')
        for key, value in options.items():
            out.append('<button class="opt" data-opt="%s"><span class="ol">%s</span><span class="ot">%s</span></button>' % (attr(key), attr(key), base.inline(value)))
        out.append('</div>')
    else:
        out.append('<textarea class="attempt" placeholder="先写推导、计算或英文作答，再查看解析；内容仅保存在本机。" aria-label="%s 作答"></textarea>' % attr(q['id']))
        out.append('<button class="rev-btn">点击显示答案解析 ▾</button>')
    out.append('<div class="sol hidden"><div class="sol-body">%s</div></div>' % base.blocks(q['solution']))
    out.append('<p class="source">来源：%s</p></div>' % attr(q['source']))
    return '\n'.join(out)


def build(data, input_dir=None):
    """Build HTML. Relative figure paths require the input JSON directory."""
    validate(data)
    chapters, questions = data['chapters'], data['questions']
    question_chapters = {q['chapter'] for q in questions}
    title = html.escape(data['title'])
    body = ['<header class="hero"><div class="hero-inner"><div><h1>%s</h1><div class="sub">%s</div></div><button id="theme-btn">主题:自动</button><div class="prog"><span id="head-progress"></span><div class="bar" id="head-bar"><i></i></div></div></div></header><main>' % (title, html.escape(data['status']))]
    if data.get('sidebar'):
        body[0]=body[0][:-len('<main>')]
        body.append('<div class="review-layout"><aside class="side-shell"><button id="side-toggle" aria-controls="chapter-sidebar" aria-expanded="false">章节导航 ▾</button><nav class="side" id="chapter-sidebar" aria-label="章节导航"><div class="side-title">章节导航</div><p class="side-hint">进度为已查看解析，非掌握程度</p>')
        for c in chapters:
            body.append('<div class="side-group"><a class="side-item" data-ch="%s" href="#%s"><span class="side-t">%s</span><span class="side-n">0/0</span><span class="side-b"><i></i></span></a>' % (c['id'],c['id'],html.escape(c['title'])))
            if c.get('sections'):
                body.append('<details class="side-sections"><summary>%s · 小节目录</summary>' % html.escape(c['title'].split(' · ')[0]))
                for s in c['sections']:
                    body.append('<a href="#%s">%s%s</a>' % (html.escape(s['id']),html.escape(s['title']),('<span class="side-en" lang="en">'+html.escape(s['english_title'])+'</span>') if s.get('english_title') else ''))
                body.append('</details>')
            if c['id'] in question_chapters: body.append('<a class="side-practice" href="#practice-%s">本部分练习 →</a>' % c['id'])
            body.append('</div>')
        body.append('<a class="side-back" href="#learning-index">完整讲解目录 ↑</a></nav></aside><main>')
        if not any(c.get('sections') for c in chapters):
            body[-1]=body[-1].replace('<a class="side-back" href="#learning-index">完整讲解目录 ↑</a>','')
    else:
        body.append('<nav>' + ' · '.join('<a href="#%s">%s</a>' % (c['id'], html.escape(c['title'])) for c in chapters) + '</nav>')
    if any(c.get('sections') for c in chapters):
        body.append('<section class="chapter learning-index" id="learning-index"><h2>讲解目录 · 按讲义顺序阅读</h2><p>展开一讲，按 PPT 页段继续阅读。数学基础在需要时插入；每讲读完再做练习。</p>')
        if any(s.get('bilingual') for c in chapters for s in c.get('sections',[])):
            body.append('<p class="source">每节先列符号，再用 English + 中文解释对应核心概念；范例证明另逐步对照。英文为依据材料整理的复习表述，非讲义逐字引文或官方答案。</p>')
        for c in chapters:
            body.append('<details%s><summary>%s</summary><ul>' % ('' if data.get('collapse_index') else ' open',html.escape(c['title'])))
            for s in c.get('sections', []):
                body.append('<li><a href="#%s">%s</a></li>' % (html.escape(s['id']),html.escape(s['title'])))
            if c['id'] in question_chapters: body.append('<li><a href="#practice-%s">完成本部分精选题 →</a></li></ul></details>' % c['id'])
            else: body.append('</ul></details>')
        body.append('</section>')
    if questions: body.append('<section class="chapter controls"><label>搜索 <input id="search" placeholder="题号 / 考点 / 关键词"></label><label>难度 <select id="difficulty"><option value="">全部</option><option>基础</option><option>进阶</option><option>综合</option></select></label><label>练习范围 <select id="mode"><option value="all">全部题</option><option value="wrong">错题</option><option value="bookmarked">收藏 / 待重做</option><option value="unanswered">未作答</option></select></label><button id="exam-mode" hidden>开始计时闭卷练习</button><button id="finish-exam" hidden>结束闭卷练习</button><span id="timer"></span><p id="filter-count"></p></section>')
    for c in chapters:
        body.append('<section class="chapter" id="%s"><h2 class="ch-title">%s</h2><p class="source">%s</p><div class="chapter-notes">%s</div>' %
                    (c['id'], html.escape(c['title']), html.escape(c['source']), base.blocks(c['notes'])))
        for s in c.get('sections', []):
            pairs=''.join('<div class="bilingual-pair"><p class="english" lang="en"><strong>English</strong> %s</p><p class="chinese"><strong>中文解释</strong> %s</p></div>' % (base.inline(p['en']),base.inline(p['zh'])) for p in s.get('bilingual',[]))
            en_title=('<span class="lesson-en" lang="en">%s</span>' % html.escape(s['english_title'])) if s.get('english_title') else ''
            notation=('<div class="notation"><strong>先认识这里的符号</strong>%s</div>' % base.blocks(s['symbols'])) if s.get('symbols') else ''
            pages=('<p class="source">对应讲义：%s</p>' % html.escape(s['pages'])) if s.get('pages') else ''
            body.append('<article class="chapter-notes lesson" id="%s"><h3>%s%s</h3>%s%s%s%s<p class="lesson-links"><a href="#learning-index">↑ 返回讲解目录</a> · <a href="#practice-%s">本讲练习 →</a></p></article>' % (html.escape(s['id']),html.escape(s['title']),en_title,pages,notation,pairs,base.blocks(s['body']),c['id']))
        if c['id'] not in question_chapters:
            body = [item.replace(' · <a href="#practice-%s">本讲练习 →</a>' % c['id'], '') for item in body]
        for figure in c.get('figures',[]):
            path=Path(figure['path'])
            if not path.is_absolute():
                if input_dir is None: raise ValueError('Relative figure paths require input_dir')
                path=Path(input_dir)/path
            encoded=base64.b64encode(path.read_bytes()).decode('ascii')
            mime={'.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.gif':'image/gif','.webp':'image/webp'}[path.suffix.lower()]
            body.append('<figure class="lecture-figure"><img src="data:%s;base64,%s" alt="%s"><figcaption>%s</figcaption></figure>' % (mime,encoded,html.escape(figure['caption']),html.escape(figure['caption'])))
        if c['id'] in question_chapters: body.append('<h3 id="practice-%s">精选练习 · %s</h3>' % (c['id'],html.escape(c['title'])))
        for q in questions:
            if q['chapter'] == c['id']:
                lesson_href=data.get('lesson_base','')+'#'+q.get('lesson_id',c['id'])
                body.append(render_question(q).replace('<div class="qtext">', '<p class="learning-purpose">本题独特训练点：%s · <a href="%s">回看对应讲解</a></p><div class="qtext">' % (html.escape(q.get('unique_focus',q.get('family',''))),html.escape(lesson_href)),1))
        body.append('</section>')
    if questions: body.append('<div class="final-stats" id="final-stats"></div><button class="reset">重置全部作答</button></main><div id="selfcheck" hidden></div>')
    if not questions:
        body.append('</main><div id="selfcheck" hidden></div>')
    if data.get('sidebar'):
        body.append('</div>')
    digest = data.get('storage_digest') or hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    config = {'storage': 'ai_review_' + digest, 'sections': [[c['id'], c['title']] for c in chapters], 'examMinutes': data.get('exam_minutes')}
    js = 'window.REVIEW_CONFIG=' + json.dumps(config, ensure_ascii=True).replace('<', '\\u003c') + ';\n' + Path(__file__).with_name('review_state.js').read_text(encoding='utf-8') + '\n' + Path(__file__).with_name('review.js').read_text(encoding='utf-8')
    assets = Path(base.ASSET_DIR)
    scripts = [(assets / n).read_text(encoding='utf-8') for n in ('katex.min.js', 'auto-render.min.js')]
    extras = ''
    if data.get('sidebar'):
        extras += r'''
        (function(){
          var nav=document.getElementById('chapter-sidebar'), toggle=document.getElementById('side-toggle');
          var hero=document.querySelector('header.hero'), pending=false;
          var headings=Array.from(document.querySelectorAll('main section.chapter[id],main article.lesson[id],main h3[id]'));
          function update(){
            pending=false;
            var mobile=matchMedia('(max-width:900px)').matches;
            var height=mobile?0:hero.getBoundingClientRect().height;
            document.documentElement.style.setProperty('--hero-height',height+'px');
            var active=null,offset=height+(mobile?65:30);
            headings.forEach(function(el){if(el.getClientRects().length&&el.getBoundingClientRect().top<=offset)active=el;});
            var section=active&&active.closest('section.chapter[id]');
            nav.querySelectorAll('.side-item').forEach(function(a){
              var on=!!section&&a.dataset.ch===section.id;
              a.classList.toggle('active',on);
              if(on)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');
            });
            nav.querySelectorAll('.side-sections a,.side-practice').forEach(function(a){
              a.classList.toggle('current',!!active&&a.getAttribute('href')==='#'+active.id);
            });
          }
          function schedule(){if(!pending){pending=true;requestAnimationFrame(update);}}
          toggle.addEventListener('click',function(){var open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));nav.classList.toggle('mobile-open',open);});
          nav.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){toggle.setAttribute('aria-expanded','false');nav.classList.remove('mobile-open');schedule();});});
          window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);
          window.addEventListener('hashchange',schedule);window.addEventListener('load',schedule);
          new ResizeObserver(schedule).observe(hero);update();
        })();
        '''
    scripts += [js, extras]
    css=''' .source{font-size:12px;color:var(--muted)} nav{margin:12px 0}a{color:var(--accent)}.fs-row{flex-wrap:wrap}.q[hidden]{display:none}.controls{display:flex;gap:12px;flex-wrap:wrap}.controls label{display:flex;gap:6px;align-items:center}input,select,textarea{font:inherit;color:var(--text);background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px}textarea{display:block;width:100%;min-height:110px;margin:10px 0}.bookmark{margin-left:auto;cursor:pointer}.bookmarked{border:2px solid var(--accent2)}.q-top{flex-wrap:wrap}.lecture-figure{margin:16px 0}.lecture-figure img{max-width:100%;height:auto}.lecture-figure figcaption{color:var(--muted);font-size:12px}.exam-active .sol,.exam-active .lecture-figure,.exam-active .source{display:none!important}.exam-active .opt.correct,.exam-active .opt.wrong{color:var(--text)!important;background:var(--card)!important;border-color:var(--line)!important}.exam-active .chapter>.ch-title~p,.exam-active .chapter>.ch-title~ul,.exam-active .chapter>.ch-title~ol,.exam-active .chapter>.ch-title~.tbl-wrap{display:none}@media print{header.hero{position:static}.controls,.bookmark,.reset,.rev-btn,textarea{display:none}.sol{display:block!important}.q{break-inside:avoid}}'''
    css += '.exam-active .chapter-notes,.exam-active #final-stats{display:none!important}'
    css += '.lesson{padding:18px 0;border-top:1px solid var(--line);line-height:1.95}.lesson h3{font-size:22px;color:var(--accent)}.learning-index ul{columns:2}.learning-index li{break-inside:avoid;margin:8px 0}.lesson-links{font-size:14px}.learning-purpose{background:var(--bg);padding:12px;border-radius:8px;font-size:14px}html{scroll-behavior:smooth}article[id],h3[id],section[id]{scroll-margin-top:110px}.exam-active .learning-index,.exam-active .learning-purpose,.exam-active nav{display:none!important}.katex-display{overflow-x:auto;overflow-y:hidden}@media(max-width:700px){.learning-index ul{columns:1}.lesson h3{font-size:19px}}'
    css += 'html{scroll-behavior:auto}.mi{display:inline-block;max-width:100%;overflow-x:auto;vertical-align:middle;padding:2px 0}.lesson p,.source,.qtext,.sol-body{overflow-wrap:anywhere}article[id],h3[id],section[id]{scroll-margin-top:130px}@media(max-width:700px){header.hero{position:static}article[id],h3[id],section[id]{scroll-margin-top:16px}.controls label{flex-wrap:wrap;max-width:100%}.controls input,.controls select{max-width:100%}.final-stats .fs-row>span{min-width:0!important}}'
    css += '.notation{background:var(--bg);border-left:4px solid var(--accent);border-radius:6px;padding:14px 18px;margin:16px 0;font-size:15px}.notation p{margin-bottom:0;overflow-wrap:anywhere}.learning-index summary{cursor:pointer;font-weight:600;padding:10px 0}.learning-index details+details{border-top:1px solid var(--line)}'
    css += '.lesson-en{display:block;font-size:16px;font-weight:500;color:var(--muted);margin-top:4px}.bilingual-pair{margin:20px 0;padding:14px 18px;border:1px solid var(--line);border-radius:10px}.bilingual-pair .english{font-size:16px;line-height:1.8;margin:0 0 10px}.bilingual-pair .chinese{margin:0;line-height:1.9}.bilingual-pair strong{display:block;font-size:12px;color:var(--accent);letter-spacing:.04em}.side-en{display:block;font-size:10px;color:var(--muted);margin-top:2px}'
    if data.get('sidebar'):
        css += '''
        :root{--hero-height:100px}.hero-inner{max-width:1320px}
        .review-layout{display:grid;grid-template-columns:260px minmax(0,960px);gap:22px;max-width:1320px;margin:0 auto;padding:20px 20px 60px;align-items:start}
        .review-layout main{min-width:0;width:100%;max-width:none;padding:0;margin:0}
        .side-shell{position:sticky;top:calc(var(--hero-height) + 16px);min-width:0}
        nav.side{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;box-shadow:var(--shadow);max-height:calc(100dvh - var(--hero-height) - 32px);overflow:auto;overscroll-behavior:contain}
        .side-title{font-size:17px;font-weight:700;padding:4px 8px}.side-hint{font-size:11px;color:var(--muted);padding:0 8px;margin:4px 0 12px}
        .side-group{margin:5px 0 9px}.side-item{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:5px;padding:10px;border:1px solid transparent;border-radius:9px;text-decoration:none;color:var(--text)}
        .side-item:hover,.side-item.active{background:var(--bg);border-color:var(--accent)}.side-item.active{box-shadow:inset 3px 0 var(--accent)}
        .side-t{font-size:13px;font-weight:600;overflow-wrap:anywhere}.side-n{font-size:11px;color:var(--muted);align-self:center}.side-item.done .side-t{color:var(--good)}
        .side-b{grid-column:1/-1;height:4px;background:var(--line);border-radius:99px;overflow:hidden}.side-b i{display:block;height:100%;width:0;background:var(--accent);transition:width .2s}
        .side-sections{margin:0 8px;font-size:12px}.side-sections summary{cursor:pointer;padding:6px 0;color:var(--muted)}
        .side-sections a{display:block;padding:6px 8px;border-left:2px solid var(--line);text-decoration:none;color:var(--text);overflow-wrap:anywhere}
        .side-sections a:hover,.side-sections a.current{color:var(--accent);background:var(--bg);border-color:var(--accent)}
        .side-practice,.side-back{display:block;padding:4px 16px;font-size:12px}.side-practice.current{font-weight:700}.side-back{border-top:1px solid var(--line);padding-top:10px}
        #side-toggle{display:none}.review-layout [id]{scroll-margin-top:calc(var(--hero-height) + 24px)}
        .exam-active .side-shell{display:none}.exam-active .review-layout{grid-template-columns:minmax(0,960px);justify-content:center}
        @media(max-width:900px){header.hero{position:static}.review-layout{display:block;padding:12px}.side-shell{top:0;z-index:40;margin-bottom:16px;background:var(--bg)}
          #side-toggle{display:block;width:100%;padding:12px 16px;font:inherit;font-weight:700;text-align:left;color:var(--text);background:var(--card);border:1px solid var(--line);border-radius:10px;cursor:pointer}
          nav.side{display:none;max-height:calc(75dvh - 50px)}nav.side.mobile-open{display:block;margin-top:5px}.review-layout [id]{scroll-margin-top:64px}.side-t{font-size:14px}
        }
        @media print{.side-shell{display:none}.review-layout{display:block;padding:0}}
        '''
    css += '.exam-active .rev-btn,.exam-active .reset,.exam-active .prog,.exam-active #selfcheck{display:none!important}.opt.selected{outline:2px solid var(--accent)}.exam-active .opt .ol{background:var(--panel)!important;border-color:var(--line)!important;color:var(--text)!important}.exam-active .opt{animation:none!important}'
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s\n%s\n%s</style></head><body>%s%s</body></html>' % (title, base.katex_css_inline(), base.CSS, css, '\n'.join(body), ''.join('<script>%s</script>' % s for s in scripts))


def main():
    parser = argparse.ArgumentParser(description='Build a self-contained offline review (Python 3.9+).')
    parser.add_argument('input', type=Path, help='Input JSON; relative image paths resolve beside this file')
    parser.add_argument('output', type=Path, help='Output HTML')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8-sig'))
        result = build(data, args.input.resolve().parent)
        args.output.write_text(result, encoding='utf-8')
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print('Written %s: %d questions' % (args.output, len(data['questions'])))


if __name__ == '__main__':
    main()
