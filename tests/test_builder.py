import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_review import build
from schema import validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / 'fixtures'

def fixture():
    return {'title':'Synthetic review <script>alert(1)</script>','status':'Synthetic only', 'sidebar':True,'exam_minutes':5,
      'chapters':[{'id':'unit-1','title':'Unit <one>','source':'Synthetic source','notes':'$a<b$ and $a>b$. [safe](https://example.com) [unsafe](javascript:alert(1))',
        'sections':[{'id':'lesson-1','title':'Example','english_title':'Example lesson','symbols':'$x$ is a variable','pages':'1–2','body':r'$$\begin{matrix}1&2\\3&4\end{matrix}$$', 'bilingual':[{'en':'A useful example.','zh':'合成示例。'}]}]}],
      'questions':[{'id':'Q1','chapter':'unit-1','lesson_id':'lesson-1','type':'mcq','text':'Pick $1<2$. <img src=x onerror=alert(1)>','options':{'A':'Yes','B':'No'},'answer':'A','solution':'A is correct.','source':'Synthetic','points':2,'difficulty':'基础'},
        {'id':'Q2','chapter':'unit-1','type':'tf','text':'One equals one.','answer':'T','solution':'True.','source':'Synthetic'},
        {'id':'Q3','chapter':'unit-1','type':'reveal','text':'Explain $x<y$.','solution':'Explain the relation.','source':'Synthetic'}]}

class BuilderTest(unittest.TestCase):
    def test_variants(self):
        for name in ('mixed','reveal','notes'):
            data=json.loads((FIXTURES/(name+'.json')).read_text());doc=build(data,FIXTURES)
            self.assertIn('window.REVIEW_CONFIG=',doc)
            if name=='notes':
                self.assertNotIn('class="chapter controls"',doc);self.assertNotIn('class="final-stats"',doc);self.assertNotIn('id="practice-',doc)
    def test_repeat_and_escape(self):
        data=fixture();a=build(data);self.assertEqual(a,build(data))
        self.assertIn('a&lt;b',a);self.assertIn('1&amp;2',a)
        self.assertNotIn('<img src=x',a);self.assertNotIn('<script>alert(1)',a)
        self.assertNotIn('href="javascript:',a);self.assertNotIn('url(fonts/',a)
    def test_bad_inputs(self):
        changes=[lambda d:d['questions'].append(copy.deepcopy(d['questions'][0])),lambda d:d['chapters'][0]['sections'].append(copy.deepcopy(d['chapters'][0]['sections'][0])),lambda d:d['questions'][0].update(lesson_id='missing'),lambda d:d['questions'][0].update(points=True),lambda d:d['questions'][0].update(answer='Z'),lambda d:d['questions'][0].update(options=['a']),lambda d:d.update(lesson_base='javascript:alert(1)'),lambda d:d.update(exam_minutes=0),lambda d:d['questions'][0].update(text=7),lambda d:d['chapters'][0].update(sections={}),lambda d:d.update(storage_digest=''),lambda d:d['questions'][0].update(id='__proto__')]
        for change in changes:
            data=fixture();change(data)
            with self.assertRaises(ValueError):validate(data)
    def test_digest(self):
        def storage(d):return re.search(r'"storage": "([^"]+)"',build(d)).group(1)
        data=fixture();old=storage(data);data['questions'][0]['answer']='B';self.assertNotEqual(old,storage(data))
        data['storage_digest']='0123456789abcdef';old=storage(data);data['title']='New';self.assertEqual(old,storage(data))
    def test_cli_image_and_optimized_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);data=fixture();data['chapters'][0]['figures']=[{'path':'image.svg','caption':'Image'}]
            (p/'image.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>')
            (p/'input.json').write_text(json.dumps(data))
            cmd=[sys.executable,'-O',str(ROOT/'scripts/build_review.py')]
            run=subprocess.run(cmd+[str(p/'input.json'),str(p/'output.html')],cwd='/',capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('data:image/svg+xml;base64,',(p/'output.html').read_text())
            data['questions'][0]['answer']='Z';(p/'input.json').write_text(json.dumps(data))
            self.assertNotEqual(subprocess.run(cmd+[str(p/'input.json'),str(p/'output.html')],cwd='/',capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(cmd+['--help'],cwd='/',capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
