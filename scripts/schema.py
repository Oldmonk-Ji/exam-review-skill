"""Explicit, optimization-safe validation for review JSON (Python 3.9+)."""
import math
import re
from pathlib import Path
from urllib.parse import urlsplit


def validate(data):
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    def obj(value, name):
        require(isinstance(value, dict), name + ' must be an object')
    def string(value, name, nonempty=False):
        require(isinstance(value, str), name + ' must be a string')
        require(not nonempty or bool(value.strip()), name + ' must not be empty')
        require(not any(ord(c) < 32 and c not in '\n\r\t' for c in value), name + ' contains control characters')
    def seq(value, name):
        require(isinstance(value, list), name + ' must be an array')
    obj(data, 'review')
    for key in ('title', 'status'): string(data.get(key), key, key == 'title')
    chapters, questions = data.get('chapters'), data.get('questions')
    seq(chapters, 'chapters'); seq(questions, 'questions')
    require(bool(chapters), 'At least one chapter is required')
    reserved = {'learning-index','theme-btn','head-progress','head-bar','search','difficulty','mode','exam-mode','finish-exam','timer','filter-count','final-stats','selfcheck','side-toggle','chapter-sidebar'}
    ids = set(reserved)
    def identifier(value, name):
        string(value, name, True)
        require(bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', value)), name + ' must contain ASCII letters, numbers or hyphens')
        require(value not in ids, 'Duplicate or reserved ID: ' + value)
        ids.add(value)
    chapter_ids = set()
    lessons = {}
    for c in chapters:
        obj(c, 'chapter'); identifier(c.get('id'), 'chapter.id')
        chapter_ids.add(c['id'])
        for key in ('title','source','notes'): string(c.get(key), 'chapter.' + key, key == 'title')
    for cid in chapter_ids:
        require('practice-' + cid not in ids, 'ID collides with generated practice heading')
        ids.add('practice-' + cid)
    for c in chapters:
        sections = c.get('sections', [])
        seq(sections, 'sections'); lessons[c['id']] = {c['id']}
        for s in sections:
            obj(s, 'section'); identifier(s.get('id'), 'section.id'); lessons[c['id']].add(s['id'])
            for key in ('title','body'): string(s.get(key), 'section.' + key, key == 'title')
            for key in ('english_title','symbols','pages'):
                if key in s: string(s[key], 'section.' + key)
            seq(s.get('bilingual', []), 'bilingual')
            for pair in s.get('bilingual', []):
                obj(pair, 'bilingual pair')
                for key in ('en','zh'): string(pair.get(key), 'bilingual.' + key, True)
        seq(c.get('figures', []), 'figures')
        for f in c.get('figures', []):
            obj(f, 'figure'); string(f.get('path'), 'figure.path', True); string(f.get('caption'), 'figure.caption')
            require(Path(f['path']).suffix.lower() in ('.png','.svg','.jpg','.jpeg','.gif','.webp'), 'Unsupported figure extension')
    for q in questions:
        obj(q, 'question'); identifier(q.get('id'), 'question.id')
        string(q.get('chapter'), 'question.chapter')
        require(q['chapter'] in chapter_ids, 'Unknown question chapter')
        string(q.get('type'), 'question.type')
        require(q['type'] in ('mcq','tf','reveal'), 'Unknown question type')
        for key in ('text','solution','source'): string(q.get(key), 'question.' + key, True)
        for key in ('difficulty','family','unique_focus'):
            if key in q: string(q[key], 'question.' + key)
        if 'lesson_id' in q:
            string(q['lesson_id'], 'lesson_id')
            require(q['lesson_id'] in lessons[q['chapter']], 'lesson_id must reference this chapter or one of its sections')
        points = q.get('points', 1)
        require(type(points) in (int, float) and math.isfinite(points) and points > 0, 'points must be a positive finite number')
        if 'answer' in q: string(q['answer'], 'answer')
        if q['type'] == 'mcq':
            opts = q.get('options'); obj(opts, 'options')
            require(len(opts) >= 2, 'MCQ needs at least two options')
            for k, v in opts.items():
                string(k, 'option key'); require(bool(re.fullmatch('[A-Z]', k)), 'Option keys must be single uppercase letters'); string(v, 'option value', True)
            require(q.get('answer') in opts, 'MCQ answer must identify an option')
        elif q['type'] == 'tf': require(q.get('answer') in ('T','F'), 'TF answer must be T or F')
        elif 'options' in q: require(q['options'] == {}, 'Reveal questions cannot have options')
    for key in ('sidebar','collapse_index'):
        if key in data: require(type(data[key]) is bool, key + ' must be boolean')
    if 'storage_digest' in data:
        string(data['storage_digest'], 'storage_digest')
        require(bool(re.fullmatch('[a-f0-9]{16}', data['storage_digest'])), 'storage_digest must be 16 lowercase hex characters')
    if 'exam_minutes' in data:
        value = data['exam_minutes']
        require(type(value) in (int,float) and math.isfinite(value) and value > 0, 'exam_minutes must be positive and finite')
    if 'lesson_base' in data:
        value = data['lesson_base']; string(value, 'lesson_base')
        require(not any(c.isspace() for c in value) and '\\' not in value, 'Invalid lesson_base')
        parsed = urlsplit(value)
        require(parsed.scheme in ('','http','https') and not value.startswith('//'), 'lesson_base must be relative or HTTP(S)')
        require(not parsed.fragment, 'lesson_base cannot contain a fragment')
