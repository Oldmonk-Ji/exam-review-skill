# -*- coding: utf-8 -*-
"""Smoke-test an interactive review HTML with headless Edge/Chrome.

Opens the page, waits for KaTeX rendering, then reads the page's #selfcheck
JSON (written by the builder's JS) and counts rendered math nodes on the
script-stripped DOM.

Usage: python tools/verify_html.py path/to/page.html
Exit code 0 = all checks passed, 1 = failed, 2 = setup problem.
"""
import os, re, sys, json, shutil, subprocess, tempfile

def find_browser():
    cands = [
        os.path.join(os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)'),
                     'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', r'C:\Program Files'),
                     'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', r'C:\Program Files'),
                     'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', r'C:\Users\Public'),
                     'Google', 'Chrome', 'Application', 'chrome.exe'),
    ]
    for c in cands:
        if os.path.isfile(c):
            return c
    for c in ('msedge', 'chrome', 'chromium', 'google-chrome'):
        if shutil.which(c):
            return c
    return None

def main():
    if len(sys.argv) < 2:
        print('usage: python verify_html.py path/to/page.html')
        sys.exit(2)
    page = os.path.abspath(sys.argv[1])
    if not os.path.isfile(page):
        print('page not found:', page)
        sys.exit(2)
    browser = find_browser()
    if not browser:
        print('no Edge/Chrome found')
        sys.exit(2)
    url = 'file:///' + page.replace('\\', '/').replace(' ', '%20')
    # mkdtemp + tolerant cleanup: on Windows a lingering browser child can keep
    # the dump file locked when TemporaryDirectory tries to delete it.
    tmp = tempfile.mkdtemp()
    try:
        dom_file = os.path.join(tmp, 'dom.html')
        with open(dom_file, 'w', encoding='utf-8') as out:
            subprocess.run([browser, '--headless=new', '--disable-gpu',
                            '--user-data-dir=' + os.path.join(tmp, 'profile'),
                            '--virtual-time-budget=9000', '--dump-dom', url],
                           stdout=out, stderr=subprocess.DEVNULL, timeout=120)
        with open(dom_file, encoding='utf-8', errors='replace') as f:
            dom = f.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    m = re.search(r'<div id="selfcheck"[^>]*>(.*?)</div>', dom, re.S)
    report = {'file': os.path.basename(page), 'browser': os.path.basename(browser)}
    if m:
        try:
            report['selfcheck'] = json.loads(m.group(1))
        except Exception:
            report['selfcheck'] = {'raw': m.group(1)[:200]}
    # strip <script> before counting: katex.min.js source contains the
    # literal string 'katex-error', which would cause false positives.
    stripped = re.sub(r'<script.*?</script>', '', dom, flags=re.S)
    report['katexNodes'] = len(re.findall(r'class="katex"', stripped))
    report['katexErrors'] = stripped.count('katex-error')
    sc = report.get('selfcheck') or {}
    report['ok'] = bool(
        m and sc.get('katexLoaded') is True and sc.get('katexErrors') == 0
        and not sc.get('missingAnswers') and (sc.get('questions') or 0) > 0
        and report['katexNodes'] > 0)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report['ok'] else 1)

if __name__ == '__main__':
    main()
