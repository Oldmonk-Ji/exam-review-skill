# -*- coding: utf-8 -*-
"""Build DASE7501_Interactive_Review.html from the two markdown sources."""
import re, html, io, json, os, base64

BOOK = 'DASE7501_English_Exam_Review_L1-5.md'
PAPER = 'DASE7501_Practice_Paper_L1-5.md'
OUT = 'DASE7501_Interactive_Review.html'
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'katex_assets')

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

# ---------------- math / inline / blocks ----------------

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
    rows = []
    for r in tbl:
        cells = [c.strip() for c in r.strip('|').split('|')]
        rows.append(cells)
    rows = [r for r in rows if not all(re.fullmatch(r'[-: ]+', c or '-') for c in r)]
    out = ['<div class="tbl-wrap"><table>']
    for ri, r in enumerate(rows):
        tag = 'th' if ri == 0 else 'td'
        out.append('<tr>' + ''.join('<%s>%s</%s>' % (tag, inline(c), tag) for c in r) + '</tr>')
    out.append('</table></div>')
    return ''.join(out)

def figure_html(path, caption):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), path.replace('/', os.sep))
    if not os.path.exists(p):
        WARNINGS.append('figure missing: ' + path)
        return '<p class="fig-missing">[Figure missing: %s]</p>' % html.escape(path)
    b64 = base64.b64encode(open(p, 'rb').read()).decode('ascii')
    cap = inline(caption) if caption else ''
    return ('<figure class="fig"><img src="data:image/png;base64,%s" alt="%s" loading="lazy">'
            '<figcaption>%s</figcaption></figure>' % (b64, html.escape(caption), cap))

def blocks(text):
    lines = text.split('\n')
    out = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith('!['):
            m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', s)
            if m:
                out.append(figure_html(m.group(2), m.group(1)))
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
               not lines[i].strip().startswith(('|', '>', '![')) and
               not re.match(r'^\d+\.\s', lines[i].strip()) and
               not lines[i].strip().startswith('- ')):
            par.append(lines[i].strip())
            i += 1
        out.append('<p>%s</p>' % inline(' '.join(par)))
    return '\n'.join(out)

# ---------------- question model ----------------

TYPE_ZH = {
    'Multiple choice': '选择题', 'True/False': '判断题', 'Calculation': '计算题',
    'Short answer': '简答题', 'Open question': '开放题',
}
TAG_CLS = {'选择题': 'tag-mcq', '判断题': 'tag-tf'}

def classify_quote(first):
    s = first.strip()
    if 'Solution' in s or '详解' in s or re.search(r'\[\*\*Q\d+', s):
        return 'solution'
    if re.search(r'\*\*\[(Multiple choice|True/False|Calculation|Short answer|Open question)', s):
        return 'question'
    return 'content'

def strip_q(l):
    s = l.strip()
    return s[1:].lstrip(' ') if s.startswith('>') else s

def make_question(qlines, sol_lines, sol_raw):
    first = qlines[0]
    first_s = strip_q(first)
    m = re.search(r'\*\*\[([^\]]+)\]\*\*', first_s)
    label = m.group(1) if m else 'Question'
    if 'Multiple choice' in label:
        qtype = 'mcq'
    elif 'True/False' in label:
        qtype = 'tf'
    else:
        qtype = 'reveal'
    body = [strip_q(l) for l in qlines[1:]]
    opts = []
    text_lines = []
    if m:
        rest = first_s[m.end():].strip()
        if rest:
            text_lines.append(rest)
    else:
        text_lines.append(first_s)
    for l in body:
        om = re.match(r'^([A-D])\.\s+(.*)$', l)
        if om and qtype == 'mcq':
            opts.append((om.group(1), om.group(2)))
        else:
            text_lines.append(l)
    qtext = blocks('\n'.join(text_lines))
    if qtype == 'mcq' and not opts:
        WARNINGS.append('mcq without options -> reveal: ' + first[:60])
        qtype = 'reveal'
    answer = ''
    soltext = blocks('\n'.join(strip_q(l) for l in sol_lines[1:]))
    if qtype == 'mcq':
        am = re.search(r'Answer \(答案\):\s*([A-D])', sol_raw)
        if am:
            answer = am.group(1)
        else:
            WARNINGS.append('mcq without answer -> reveal: ' + first[:60])
            qtype = 'reveal'
    elif qtype == 'tf':
        am = re.search(r'Answer \(答案\):\s*(True|False)', sol_raw)
        if am:
            answer = 'T' if am.group(1) == 'True' else 'F'
        else:
            WARNINGS.append('tf without answer -> reveal: ' + first[:60])
            qtype = 'reveal'
    return {'type': qtype, 'tag': TYPE_ZH.get(label, '题目'), 'text': qtext,
            'opts': opts, 'answer': answer, 'sol': soltext}

# ---------------- parse book ----------------

def parse_book(text):
    lines = strip_frontmatter(text.split('\n'))
    chapters = {}
    cur = None       # 'ch1'..'ch5', 'formula', 'glossary', 'mock'
    h2 = None
    h3 = None
    panel_buf = []   # lines of current ### panel
    quote_buf = []
    pending_q = None
    h1text = {}

    def flush_panel():
        nonlocal panel_buf, h3
        if h3 is not None and panel_buf:
            chapters[cur].append({'type': 'panel', 'title': h3, 'body': blocks('\n'.join(panel_buf))})
        panel_buf = []
        h3 = None

    def flush_quote():
        nonlocal quote_buf, pending_q
        if not quote_buf:
            return
        kind = classify_quote(quote_buf[0])
        if kind == 'content':
            if h3 is not None:
                panel_buf.extend(quote_buf)
            else:
                WARNINGS.append('quote outside panel: ' + quote_buf[0][:60])
        elif kind == 'question':
            pending_q = quote_buf
        else:  # solution
            if pending_q is not None:
                item = make_question(pending_q, quote_buf, '\n'.join(quote_buf))
                item['group'] = h2 if h2 in ('solved', 'extra') else 'solved'
                chapters[cur].append(item)
                pending_q = None
            else:
                WARNINGS.append('solution without question: ' + quote_buf[0][:60])
        quote_buf = []

    for line in lines:
        s = line.strip()
        if not s:
            if quote_buf:
                flush_quote()
            continue
        if s.startswith('# '):
            flush_quote()
            flush_panel()
            t = s[2:].strip()
            if t.startswith('Chapter'):
                num = re.match(r'Chapter (\d+)', t).group(1)
                cur = 'ch' + num
                chapters[cur] = []
                h1text[cur] = t
            elif t.startswith('Appendix A'):
                cur = 'formula'; chapters[cur] = []; h1text[cur] = t
            elif t.startswith('Appendix B'):
                cur = 'glossary'; chapters[cur] = []; h1text[cur] = t
            elif t.startswith('Appendix C'):
                cur = 'mock'; chapters[cur] = []; h1text[cur] = t
            else:
                cur = None
            h2 = h3 = None
            continue
        if s.startswith('## '):
            flush_quote()
            flush_panel()
            t = s[3:].strip()
            if 'Key Concepts' in t:
                h2 = 'concepts'; h3 = None
            elif 'Solved Examples' in t:
                h2 = 'solved'; h3 = None
            elif 'Extra Practice' in t:
                h2 = 'extra'; h3 = None
            elif cur == 'formula':
                h2 = 'formula'; h3 = t
            elif cur == 'mock':
                h2 = 'mock'; h3 = None
            elif cur == 'glossary':
                h2 = 'glossary'; h3 = None
            else:
                h2 = None; h3 = None
            if cur == 'mock':
                chapters[cur].append({'type': 'mockline', 'line': line})
            continue
        if s.startswith('### '):
            flush_quote()
            flush_panel()
            h3 = s[4:].strip()
            continue
        if s.startswith('>'):
            quote_buf.append(line)
            continue
        # plain content
        if cur is None:
            continue
        if h2 == 'concepts':
            if h3 is not None:
                panel_buf.append(line)
        elif h2 in ('solved', 'extra'):
            WARNINGS.append('stray line in ' + h2 + ': ' + s[:60])
        elif cur == 'formula' and h2 == 'formula':
            panel_buf.append(line)
        elif cur == 'glossary':
            chapters[cur].append({'type': 'glosline', 'line': line})
        elif cur == 'mock':
            chapters[cur].append({'type': 'mockline', 'line': line})

    flush_quote()
    flush_panel()

    # post-process formula chapter: panels per ##
    return chapters, h1text

# ---------------- parse glossary ----------------

def parse_glossary(chapters):
    rows = []
    for item in chapters.get('glossary', []):
        if item['type'] == 'glosline':
            s = item['line'].strip()
            if s.startswith('|') and 'English' not in s and not re.fullmatch(r'[\-|: ]+', s):
                cells = [c.strip() for c in s.strip('|').split('|')]
                if len(cells) >= 2:
                    rows.append((cells[0], cells[1]))
    return rows

# ---------------- parse mock exam (appendix C) ----------------

def parse_mock(chapters):
    lines = [it['line'] for it in chapters.get('mock', [])]
    questions = {}   # num -> dict
    sec = None
    cur = None
    buf = []
    opts = []
    def flush():
        nonlocal buf, opts
        if cur is not None:
            qtype = {'A': 'mcq', 'B': 'tf', 'C': 'reveal'}[sec]
            questions[cur] = {'type': qtype, 'num': cur,
                              'text': blocks('\n'.join(buf)), 'opts': list(opts),
                              'answer': '', 'sol': '', 'tag': {'A': '选择题', 'B': '判断题', 'C': '计算题'}[sec]}
        buf = []; opts = []
    for line in lines:
        s = line.strip()
        if s.startswith('## '):
            flush()
            cur = None
            t = s[3:]
            if 'Multiple Choice' in t:
                sec = 'A'
            elif 'True/False' in t:
                sec = 'B'
            elif 'Calculation' in t:
                sec = 'C'
            elif 'Answer Key' in t:
                sec = 'KEY'
            continue
        if sec == 'KEY':
            m = re.search(r'Section A \(选择题\)\*\*:\s*(.*)', s)
            if m:
                for a, b in re.findall(r'(\d+)-([A-D])', m.group(1)):
                    questions[a]['answer'] = b
            m = re.search(r'Section B \(判断题\)\*\*:\s*(.*)', s)
            if m:
                for a, b in re.findall(r'(\d+)-([TF])', m.group(1)):
                    questions[a]['answer'] = b
            m = re.match(r'\*\*Q(\d+)\.\*\*\s*(.*)', s)
            if m:
                questions[m.group(1)]['sol'] = blocks(m.group(2))
            continue
        if not sec or sec not in ('A', 'B', 'C'):
            continue
        m = re.match(r'\*\*Q(\d+)\.\*\*\s*(.*)', s)
        if m:
            flush()
            cur = m.group(1)
            buf = [m.group(2)]
            continue
        if cur is not None:
            om = re.match(r'^([A-D])\.\s+(.*)$', s)
            if sec == 'A' and om:
                opts.append((om.group(1), om.group(2)))
            else:
                buf.append(s)
    flush()
    # attach explanations
    for num, q in questions.items():
        if q['type'] in ('mcq', 'tf') and not q['sol']:
            q['sol'] = blocks(MOCK_EXPL.get(num, ''))
        q['ch'] = 'mock'
        q['id'] = 'mock-' + num
        q['shownum'] = 'Q' + num
    return questions

MOCK_EXPL = {
 '1': '外观(appearance)像人不是必要条件;工业机械手长得不像人但仍是机器人。必要条件:感知(sensing)、物理动作(physical actions)、可重复编程(re-programmable)、自主并与人类交互(autonomous and interactive)。',
 '2': 'ISO 定义:自动控制(automatically controlled)、可重复编程(reprogrammable)、多用途机械手(multipurpose manipulator),可在三个或更多轴上编程(programmable in three or more axes)。',
 '3': '五大组成:机械手(manipulator)、末端执行器(end effector)、执行器(actuators)、传感器(sensors)、控制器(controller);齿轮箱(gear box)不在其中。',
 '4': '元学习(meta-learning)利用以前任务的知识快速适应新任务;示范学习(demonstration)是看别人演示并模仿;探索学习(exploration)是自主试错。',
 '5': '传统工业机器人:预规划运动(pre-planned motions)、少量传感(few sensing operations)、不与人类交互(no interaction with humans)。',
 '6': '圆柱关节(cylindrical joint)提供旋转+平移(rotation + translation)两个自由度;万向关节(universal)是两个旋转;球关节(spherical)是三个旋转。',
 '7': 'SCARA 重复性最好(< 0.03 mm),用于精密、高速、轻型装配(precise, high-speed, light assembly)。',
 '8': '精度(accuracy)相对指令位置(commanded position);重复性(repeatability)相对记录/示教位置(recorded/taught position)。',
 '9': '超过 6 个自由度称为运动学冗余(kinematically redundant),冗余自由度可用于避障(obstacle avoidance)。',
 '10': '灵巧工作空间(dexterous workspace,能以任意姿态到达的点集)是可达工作空间(reachable workspace)的子集(subset)。',
 '11': '记忆陷阱:$R_y(\\beta)$ 的右上角(第 1 行第 3 列)是 $+\\sin\\beta$,左下角是 $-\\sin\\beta$,与 $R_x$、$R_z$ 的符号分布不同。',
 '12': '绕当前坐标系(current frame)旋转:右乘(post-multiply),$R = R_1 R_2$;绕固定坐标系(fixed frame)旋转:左乘(pre-multiply),$R = R_2 R_1$。',
 '13': '旋转矩阵(rotation matrix)的逆等于转置(transpose):$R^{-1} = R^T$。',
 '14': '单位四元数(unit quaternion)要求模长为 1:$q_0^2 + q_1^2 + q_2^2 + q_3^2 = 1$。',
 '15': '$q = (1,0,0,0)$ 代入四元数转矩阵公式得到单位矩阵(identity matrix),即无旋转(no rotation);绕 Z 轴转 90° 对应 $q = (\\sqrt{2}/2, 0, 0, \\sqrt{2}/2)$。',
 '16': '占空比(duty ratio / pulse-width ratio)$= t_{on} / t_{period}$,即导通时间除以周期;B 把分子分母写反。',
 '17': '旋转变压器(resolver)输出模拟量(analog),精度 > 2 角分(arc-min);光学编码器(optical encoder)输出数字量(digital),精度 < 1 角分。',
 '18': 'LVDT(线性差动变压器)精度最高(亚微米 sub-micron),量程较小(μm 到 m),用于质检自动测量与伺服位置反馈。',
 '19': '灵敏度(sensitivity)= 输出变化/输入变化(output change / input change),例如热电偶 20 mV/°C。',
 '20': '精度按满量程(full scale)百分比计算:$\\pm 1\\% \\times 10 = \\pm 0.1$ A,即 5.9--6.1 A;不是按读数(reading)的 1% 计算。',
 '21': '正运动学(forward kinematics):给定关节角(joint angles)计算工具位姿(tool pose),即从关节空间(joint space)到任务空间(task space)。',
 '22': '雅可比(Jacobian)$J = \\partial f(q)/\\partial q$ 是关节变量(joint variables)的函数,随构型(configuration)变化,不是常数矩阵。',
 '23': '伪逆(pseudo-inverse)$J^+ = (J^T J)^{-1} J^T$;B 把乘法顺序写反。通解为 $\\dot{q} = J^+ \\dot{Y} + (I - J^+ J) z$。',
 '24': 'CCD(循环坐标下降)从最远端关节(most distal joint)开始,一次只解一个关节(一维最小化),逐步向目标迭代。',
 '25': '解析法(analytical)快而精确(fast and exact),但并非对所有几何都适用——一般构型几乎不可能得到通解;数值法(numerical)才是通用解法,但计算量大且不精确。',
 '26': '可重复编程(re-programmable)是必要条件;只有外观(appearance)而没有感知、可编程与自主性,不算机器人。',
 '27': '通常重复性(repeatability)数值小于精度(accuracy):重复性只衡量相对自身均值的散布,不受标定(calibration)、模型(model)等系统误差影响。',
 '28': '绕同一轴(Z)的旋转可以相加(可交换):$R_z(30°) R_z(60°) = R_z(90°)$;绕不同轴的旋转一般不满足交换律。',
 '29': '光学编码器(optical encoder)输出数字量(digital);输出模拟量(analog)的是旋转变压器(resolver)。',
 '30': '液压执行器(hydraulic actuators)功重比大(great power-to-weight ratio),但维护成本高(high maintenance cost),且效率差(poor efficiency)。',
 '31': 'D-H 约定:$Z_i$ 轴与关节 $i+1$ 的运动轴对齐(align $Z_i$ with the motion axis of joint $i+1$);$X_i$ 沿 $Z_{i-1}$ 与 $Z_i$ 的公垂线(common normal)。',
}

# ---------------- parse practice paper ----------------

def parse_paper(text):
    lines = strip_frontmatter(text.split('\n'))
    part1, part2 = [], []
    mode = None
    for line in lines:
        if line.startswith('# Part 1'):
            mode = 'q'
            continue
        if line.startswith('# Part 2'):
            mode = 'a'
            continue
        if mode == 'q':
            part1.append(line)
        elif mode == 'a':
            part2.append(line)
    # questions
    questions = {}
    sec = None
    cur = None
    buf = []
    opts = []
    def flush():
        nonlocal buf, opts
        if cur is not None:
            questions[cur] = {'type': {'A': 'mcq', 'B': 'tf', 'C': 'reveal'}[sec], 'num': cur,
                              'text': blocks('\n'.join(buf)), 'opts': list(opts),
                              'answer': '', 'sol': '', 'tag': {'A': '选择题', 'B': '判断题', 'C': '计算题'}[sec]}
        buf = []; opts = []
    for line in part1:
        s = line.strip()
        if s.startswith('## '):
            flush()
            cur = None
            t = s[3:]
            if 'Multiple Choice' in t:
                sec = 'A'
            elif 'True/False' in t:
                sec = 'B'
            elif 'Calculation' in t:
                sec = 'C'
            continue
        m = re.match(r'\*\*Q(\d+)\.\*\*\s*(.*)', s)
        if m:
            flush()
            cur = m.group(1)
            buf = [m.group(2)]
            continue
        if cur is not None:
            om = re.match(r'^([A-D])\.\s+(.*)$', s)
            if sec == 'A' and om:
                opts.append((om.group(1), om.group(2)))
            else:
                buf.append(s)
    flush()
    # answers: MCQ/TF explanations are paragraphs, calc solutions are quote blocks
    for line in part2:
        s = line.strip()
        if s.startswith('**Section') or not s:
            continue
        if s.startswith('>'):
            continue
        m = re.match(r'\*\*Q(\d+)\.\s*([A-D])\.\*\*\s*(.*)', s)
        if m and m.group(1) in questions:
            q = questions[m.group(1)]
            q['answer'] = m.group(2)
            q['sol'] = blocks(m.group(3))
            continue
        m = re.match(r'\*\*Q(\d+)\.\s*([TF])\s*\((正确|错误)\)\.\*\*\s*(.*)', s)
        if m and m.group(1) in questions:
            q = questions[m.group(1)]
            q['answer'] = m.group(2)
            q['sol'] = blocks(m.group(3))
            continue
    cur_sol = None
    sol_buf = []
    def flush_sol():
        nonlocal sol_buf
        if cur_sol and cur_sol in questions:
            questions[cur_sol]['sol'] = blocks('\n'.join(sol_buf))
        sol_buf = []
    for line in part2:
        s = line.strip()
        if s.startswith('>') and re.match(r'>\s*\*\*\[Q(\d+)\s*详解\]\*\*', s):
            flush_sol()
            cur_sol = re.match(r'>\s*\*\*\[Q(\d+)\s*详解\]\*\*', s).group(1)
            continue
        if s.startswith('>') and cur_sol:
            sol_buf.append(s[1:].lstrip(' '))
    flush_sol()
    for num, q in questions.items():
        if not q['sol']:
            WARNINGS.append('paper question without solution: Q' + num)
        q['ch'] = 'paper'
        q['id'] = 'pp-' + num
        q['shownum'] = 'Q' + num
    return questions

# ---------------- chapter title helper ----------------

def split_h1(t):
    m = re.search(r'[\u4e00-\u9fff]', t)
    if not m:
        return t, ''
    i = m.start()
    en = t[:i].strip()
    zh = t[i:].strip()
    en = re.sub(r'^Chapter \d+\s*', '', en)
    en = re.sub(r'^Appendix [A-C]\s*', '', en)
    m2 = re.match(r'([^(]+)\(([^)]+)\)', zh)
    if m2:
        zh, lec = m2.group(1).strip(), '(' + m2.group(2).strip() + ')'
        return zh, en + ' ' + lec
    return zh, en

# ---------------- render question ----------------

def render_q(q, idx):
    cls = TAG_CLS.get(q['tag'], 'tag-reveal')
    idattr = ' data-id="%s"' % q['id']
    num_html = '<span class="qnum">%s</span>' % q['shownum']
    parts = ['<div class="q" data-ch="%s"%s data-type="%s" data-answer="%s">' % (q['ch'], idattr, q['type'], q.get('answer', ''))]
    parts.append('<div class="q-top"><span class="tag %s">%s</span>%s</div>' % (cls, q['tag'], num_html))
    parts.append('<div class="qtext">%s</div>' % q['text'])
    if q['type'] == 'mcq' and q['opts']:
        parts.append('<div class="opts">')
        for letter, txt in q['opts']:
            parts.append('<button class="opt" data-opt="%s"><span class="ol">%s</span><span class="ot">%s</span></button>' % (letter, letter, inline(txt)))
        parts.append('</div>')
    if q['type'] == 'tf':
        parts.append('<div class="opts tf"><button class="opt" data-opt="T"><span class="ol">T</span><span class="ot">True (正确)</span></button><button class="opt" data-opt="F"><span class="ol">F</span><span class="ot">False (错误)</span></button></div>')
    if q['type'] == 'reveal':
        parts.append('<button class="rev-btn">点击显示答案解析 ▾</button>')
    parts.append('<div class="sol hidden">')
    if q['type'] in ('mcq', 'tf') and q.get('answer'):
        ans_txt = q['answer'] if q['type'] == 'mcq' else ('True (正确)' if q['answer'] == 'T' else 'False (错误)')
        parts.append('<div class="sol-tag">正确答案:%s</div>' % ans_txt)
    parts.append('<div class="sol-body">%s</div></div></div>' % q['sol'])
    return '\n'.join(parts)

# ---------------- assemble page ----------------

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
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
header.hero{background:linear-gradient(120deg,var(--head-g1),var(--head-g2));
  color:#fff;padding:22px 16px;position:sticky;top:0;z-index:50;
  box-shadow:0 4px 18px rgba(30,45,90,.25)}
.hero-inner{max-width:1180px;margin:0 auto;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.hero h1{margin:0;font-size:20px;letter-spacing:.5px}
.hero .sub{font-size:12.5px;opacity:.85;margin-top:2px}
.hero .prog{margin-left:auto;display:flex;flex-direction:column;gap:4px;min-width:220px}
.hero .prog .lbl{font-size:12.5px;text-align:right}
.bar{height:8px;background:rgba(255,255,255,.25);border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;width:0;background:#fff;border-radius:99px;transition:width .4s ease}
#theme-btn{margin-left:auto;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.4);
  color:#fff;border-radius:99px;padding:5px 14px;font-size:12.5px;cursor:pointer}
#theme-btn:hover{background:rgba(255,255,255,.28)}
.layout{display:flex;gap:20px;max-width:1180px;margin:0 auto;padding:18px 16px 60px}
nav.side{width:225px;flex:none;position:sticky;top:110px;align-self:flex-start;
  background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:12px;box-shadow:var(--shadow);max-height:calc(100vh - 130px);overflow:auto}
.side-title{font-weight:700;font-size:13.5px;color:var(--muted);padding:4px 8px 8px}
.side-item{display:block;padding:8px 10px;border-radius:9px;text-decoration:none;color:var(--text);
  margin-bottom:3px;border:1px solid transparent}
.side-item:hover{background:var(--panel);border-color:var(--line)}
.side-item.done .side-t{color:var(--good)}
.side-t{font-size:13.5px;font-weight:600}
.side-n{font-size:11.5px;color:var(--muted);margin-left:4px}
.side-b{height:4px;background:var(--line);border-radius:99px;margin-top:4px;overflow:hidden}
.side-b i{display:block;height:100%;width:0;background:var(--accent);border-radius:99px;transition:width .4s}
main{flex:1;min-width:0}
.chapter{background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:22px 24px;margin-bottom:22px;box-shadow:var(--shadow)}
.ch-title{font-size:21px;margin:0 0 2px;background:linear-gradient(100deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.ch-en{font-size:13px;color:var(--muted);font-weight:400;-webkit-text-fill-color:var(--muted)}
.grp{margin:20px 0 8px;font-size:15.5px;color:var(--accent);border-left:4px solid var(--accent);
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
.ch-stats{font-size:13px;color:var(--muted);border-top:1px dashed var(--line);margin-top:16px;padding-top:10px}
.mini-bar{height:5px;background:var(--line);border-radius:99px;margin-top:5px;overflow:hidden}
.mini-bar i{display:block;height:100%;width:0;background:var(--good);transition:width .4s}
.reset{margin-top:10px;background:none;border:1px solid var(--line);color:var(--muted);
  border-radius:8px;padding:5px 14px;cursor:pointer;font:inherit;font-size:12.5px}
.reset:hover{border-color:var(--bad);color:var(--bad)}
#gloss-filter{width:100%;max-width:340px;padding:9px 14px;border:1.5px solid var(--line);
  border-radius:10px;font:inherit;background:var(--card);color:var(--text);margin-bottom:12px}
#gloss-filter:focus{outline:none;border-color:var(--accent)}
.final-stats{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 24px;
  box-shadow:var(--shadow);margin-bottom:22px}
.final-stats h3{margin:0 0 10px;color:var(--accent)}
.fs-row{display:flex;justify-content:space-between;gap:14px;font-size:13.5px;padding:5px 0;
  border-bottom:1px dashed var(--line)}
.fs-row .bar{flex:1;background:var(--line);height:7px;align-self:center}
.fs-row .bar i{background:linear-gradient(90deg,var(--accent),var(--accent2))}
.mb{margin:10px 0;overflow-x:auto}
.mi{white-space:nowrap}
.fig{margin:14px 0;text-align:center}
.fig img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:10px;background:#fff}
.fig figcaption{font-size:12.5px;color:var(--muted);margin-top:6px}
.fig-missing{color:var(--bad);font-size:12.5px}
@media (max-width:900px){
  .layout{flex-direction:column}
  nav.side{width:100%;position:static;max-height:none;display:flex;flex-wrap:wrap;gap:6px;padding:10px}
  .side-title{width:100%}
  .side-item{flex:1 1 45%;border:1px solid var(--line)}
  .hero .prog{min-width:150px}
  .chapter{padding:16px 14px}
}
'''

JS = r'''
(function(){
  var LS='dase7501_review_v1';
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
  function updateAll(){
    var grand={t:0,d:0,c:0};
    var rows=[];
    document.querySelectorAll('.chapter[data-ch]').forEach(function(ch){
      var cid=ch.dataset.ch; var t=0,d=0,c=0;
      ch.querySelectorAll('.q').forEach(function(q){
        t++;
        var st=state[q.dataset.id];
        if(q.dataset.type==='reveal'){ if(st&&st.r) d++; }
        else if(st&&st.c!==undefined){ d++; if(st.ok) c++; }
      });
      grand.t+=t; grand.d+=d; grand.c+=c;
      var el=ch.querySelector('.ch-stats');
      if(el){
        var acc=d?Math.round(100*c/d):0;
        el.innerHTML='本章共 '+t+' 题 · 已作答 '+d+' 题 · 答对 '+c+' 题 · 正确率 '+acc+'%';
        var p=t?Math.round(100*d/t):0;
        el.innerHTML+='<div class="mini-bar"><i style="width:'+p+'%"></i></div>';
      }
      var li=document.querySelector('.side-item[data-ch="'+cid+'"]');
      if(li){
        li.querySelector('.side-n').textContent=d+'/'+t;
        li.querySelector('.side-b i').style.width=(t?Math.round(100*d/t):0)+'%';
        li.classList.toggle('done', t>0 && d===t);
      }
      rows.push({cid:cid, t:t, d:d, c:c, acc:d?Math.round(100*c/d):0});
    });
    var hp=document.getElementById('head-progress');
    if(hp){
      var p=grand.t?Math.round(100*grand.d/grand.t):0;
      hp.textContent='全站进度 '+grand.d+'/'+grand.t+' ('+p+'%)';
      document.getElementById('head-bar').querySelector('i').style.width=p+'%';
    }
    var fs=document.getElementById('final-stats');
    if(fs){
      var names={ch1:'第1章 机器人导论',ch2:'第2章 工业机器人',ch3:'第3章 刚体运动',
        ch4:'第4章 执行器与传感器',ch5:'第5章 运动学',formula:'公式速查',
        glossary:'术语表',mock:'模拟卷',paper:'刷题卷'};
      var h='<h3>全站成绩单</h3>';
      rows.forEach(function(r){
        var p=r.t?Math.round(100*r.d/r.t):0;
        h+='<div class="fs-row"><span style="min-width:130px">'+(names[r.cid]||r.cid)+'</span>'+
           '<span class="bar"><i style="width:'+p+'%"></i></span>'+
           '<span style="min-width:150px;text-align:right">'+r.d+'/'+r.t+' 题 · 答对 '+r.c+' · 正确率 '+r.acc+'%</span></div>';
      });
      var tp=grand.t?Math.round(100*grand.d/grand.t):0;
      h+='<div class="fs-row"><strong>总计</strong><span class="bar"><i style="width:'+tp+'%"></i></span>'+
         '<span style="min-width:150px;text-align:right"><strong>'+grand.d+'/'+grand.t+' ('+tp+'%)</strong></span></div>';
      fs.innerHTML=h;
    }
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
      document.querySelectorAll('.q[data-ch="'+b.dataset.ch+'"]').forEach(function(q){
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
  var gf=document.getElementById('gloss-filter');
  if(gf){ gf.addEventListener('input', function(){
    var v=gf.value.trim().toLowerCase();
    document.querySelectorAll('#gloss-table tbody tr').forEach(function(tr){
      tr.style.display=(!v||tr.textContent.toLowerCase().indexOf(v)>-1)?'':'none';
    });
  }); }
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
      chapters:document.querySelectorAll('.chapter[data-ch]').length,
      questions:document.querySelectorAll('.q').length,
      mcq:document.querySelectorAll('.q[data-type="mcq"]').length,
      tf:document.querySelectorAll('.q[data-type="tf"]').length,
      reveal:document.querySelectorAll('.q[data-type="reveal"]').length,
      panels:document.querySelectorAll('details.panel').length,
      katexLoaded:!!window.katex,
      katexNodes:document.querySelectorAll('.katex').length,
      katexErrors:document.querySelectorAll('.katex-error').length,
      missingAnswers:missing
    });
  }
  window.addEventListener('load', function(){ setTimeout(selfcheck, 2000); });
})();
'''

def render_glossary(rows):
    trs = '\n'.join('<tr><td>%s</td><td>%s</td></tr>' % (inline(a), inline(b)) for a, b in rows)
    return ('<input id="gloss-filter" type="text" placeholder="输入关键词过滤术语 (例如 accuracy 或 精度)...">'
            '<div class="tbl-wrap"><table id="gloss-table"><thead><tr><th>English</th><th>中文</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % trs)

def main():
    book = read(BOOK)
    paper = read(PAPER)

    chapters, h1text = parse_book(book)
    gloss_rows = parse_glossary(chapters)
    mock_qs = parse_mock(chapters)
    paper_qs = parse_paper(paper)

    # formula chapter panels
    formula_items = chapters.get('formula', [])
    formula_panels = []
    for it in formula_items:
        if it.get('type') == 'panel' and it.get('body'):
            formula_panels.append(it)

    SIDE = [
        ('ch1', '第1章 机器人导论'), ('ch2', '第2章 工业机器人'), ('ch3', '第3章 刚体运动'),
        ('ch4', '第4章 执行器与传感器'), ('ch5', '第5章 运动学'), ('formula', '公式速查'),
        ('glossary', '术语表'), ('mock', '模拟卷'), ('paper', '刷题卷'),
    ]

    body = []
    body.append('<header class="hero"><div class="hero-inner">'
                '<div><h1>DASE7501 互动复习 · Interactive Review</h1>'
                '<div class="sub">讲义 + 例题 + 两套考卷 · 选择题点击作答 · 其余题目点击显示解析</div></div>'
                '<button id="theme-btn">主题:自动</button>'
                '<div class="prog"><span class="lbl" id="head-progress">全站进度 0/0</span>'
                '<div class="bar" id="head-bar"><i></i></div></div></div></header>')

    body.append('<div class="layout"><nav class="side"><div class="side-title">章节导航</div>')
    for cid, name in SIDE:
        body.append('<a class="side-item" data-ch="%s" href="#%s"><div><span class="side-t">%s</span>'
                    '<span class="side-n">0/0</span></div><div class="side-b"><i></i></div></a>' % (cid, cid, name))
    body.append('</nav><main>')

    total_qs = 0
    for cid, name in SIDE:
        body.append('<section class="chapter" id="%s" data-ch="%s">' % (cid, cid))
        if cid.startswith('ch') and cid in chapters:
            _zh, en = split_h1(h1text.get(cid, name))
            body.append('<h2 class="ch-title">%s <span class="ch-en">%s</span></h2>' % (html.escape(name), html.escape(en)))
            items = chapters[cid]
            concepts = [it for it in items if it.get('type') == 'panel']
            solved = [it for it in items if it.get('type') == 'q' and it.get('group') == 'solved']
            # rebuild solved/extra from items in order
            body.append('<h3 class="grp">知识梳理 · Key Concepts</h3>')
            for i, p in enumerate(concepts):
                op = ' open' if i == 0 else ''
                body.append('<details class="panel"%s><summary>%s</summary><div class="panel-body">%s</div></details>'
                            % (op, inline(p['title']), p['body']))
            for grp_key, grp_name in (('solved', '讲义例题 · Solved Examples'), ('extra', '举一反三 · Extra Practice')):
                qs = [it for it in items if it.get('group') == grp_key]
                if not qs:
                    continue
                body.append('<h3 class="grp">%s</h3>' % grp_name)
                for idx, q in enumerate(qs, 1):
                    q = dict(q)
                    q['ch'] = cid
                    q['id'] = '%s-%d' % (cid, idx)
                    q['shownum'] = '第%d题' % idx
                    body.append(render_q(q, idx))
                    total_qs += 1
            body.append('<div class="ch-stats"></div><button class="reset" data-ch="%s">重置本章</button>' % cid)
        elif cid == 'formula':
            body.append('<h2 class="ch-title">公式速查 <span class="ch-en">Formula Sheet</span></h2>')
            body.append('<h3 class="grp">考前 30 秒扫一遍</h3>')
            for i, p in enumerate(formula_panels):
                op = ' open' if i == 0 else ''
                body.append('<details class="panel"%s><summary>%s</summary><div class="panel-body">%s</div></details>'
                            % (op, inline(p['title']), p['body']))
            body.append('<div class="ch-stats"></div>')
        elif cid == 'glossary':
            body.append('<h2 class="ch-title">术语表 <span class="ch-en">English–Chinese Glossary</span></h2>')
            body.append('<p>输入关键词即可过滤,支持英文或中文(例如 accuracy、精度、四元数)。</p>')
            body.append(render_glossary(gloss_rows))
            body.append('<div class="ch-stats"></div>')
        elif cid == 'mock':
            body.append('<h2 class="ch-title">模拟卷 <span class="ch-en">Mock Exam · 100 marks · 60 min</span></h2>')
            body.append('<p><strong>Time suggestion</strong>: 60 minutes. <strong>Total</strong>: 100 marks. '
                        '本卷题目全部为英文(与真实考试一致),点击选项作答,交卷后对照 Part 2 解析。</p>')
            for i in range(1, 36):
                q = mock_qs.get(str(i))
                if not q:
                    WARNINGS.append('mock missing Q%d' % i)
                    continue
                body.append(render_q(q, i))
                total_qs += 1
            body.append('<div class="ch-stats"></div><button class="reset" data-ch="mock">重置本章</button>')
        elif cid == 'paper':
            body.append('<h2 class="ch-title">刷题卷 <span class="ch-en">Practice Paper · 110 marks · 70 min</span></h2>')
            body.append('<p><strong>Time suggestion</strong>: 70 minutes. <strong>Total</strong>: 110 marks. '
                        '本卷题目全部为英文;第 1–5 页为连续纯题目,本页答题后展开即为原书第 6 页起的答案解析。</p>')
            for i in range(1, 35):
                q = paper_qs.get(str(i))
                if not q:
                    WARNINGS.append('paper missing Q%d' % i)
                    continue
                body.append(render_q(q, i))
                total_qs += 1
            body.append('<div class="ch-stats"></div><button class="reset" data-ch="paper">重置本章</button>')
        body.append('</section>')

    body.append('<section class="final-stats" id="final-stats"></section>')
    body.append('</main></div>')
    body.append('<div id="selfcheck" style="display:none"></div>')

    html_doc = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n'
                '<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                '<title>DASE7501 互动复习</title>\n'
                '<meta name="description" content="DASE7501 机器人课程互动复习:讲义、例题与两套考卷">\n'
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

    print('written:', OUT, len(html_doc), 'bytes')
    print('total questions:', total_qs)
    print('mock questions:', len(mock_qs), '| paper questions:', len(paper_qs),
          '| glossary rows:', len(gloss_rows), '| formula panels:', len(formula_panels))
    if WARNINGS:
        print('WARNINGS (%d):' % len(WARNINGS))
        for w in WARNINGS:
            print(' -', w)

if __name__ == '__main__':
    main()
