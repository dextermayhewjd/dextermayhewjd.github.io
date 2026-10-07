"""Browser tests of real state logic: scope, identity and explicit completion."""
import functools,html,http.server,json,re,shutil,subprocess,threading,unittest
from pathlib import Path
from reading_fixture import pack

REPO = Path(__file__).resolve().parents[1]

class ReadingProgress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chrome=shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.chrome:raise unittest.SkipTest('Chrome required')
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/__reading_test__':
                    data=cls.document.encode();self.send_response(200)
                    self.send_header('Content-Type','text/html; charset=utf-8')
                    self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
                else:super().do_GET()
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(REPO)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def run_case(self,body):
        self.__class__.document='''<html><body><script src="/assets/js/reading-progress.js"></script><script>
        const report={passed:false};const check=(ok,text)=>{if(!ok)throw new Error(text)};
        try { check(!!window.ReadingProgress,'ReadingProgress missing');
        const config='''+json.dumps(pack(),ensure_ascii=False)+''';
        const m=ReadingProgress.create(config);
        '''+body+''';report.passed=true;}catch(e){report.error=e.message}
        const out=document.createElement('pre');out.id='result';out.textContent=JSON.stringify(report);
        document.body.append(out);</script></body></html>'''
        r=subprocess.run([self.chrome,'--headless','--no-sandbox','--disable-gpu',
            '--virtual-time-budget=500','--dump-dom',f'http://127.0.0.1:{self.server.server_port}/__reading_test__'],
            capture_output=True,text=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stderr[-600:]);match=re.search(r'<pre id="result">(.*?)</pre>',r.stdout,re.S)
        self.assertIsNotNone(match,'Browser result missing');report=json.loads(html.unescape(match[1]))
        self.assertTrue(report['passed'],report.get('error'))
    def test_stage_changes_do_not_complete_targets(self):
        self.run_case("m.selectView('execution');check(m.snapshot().checks.length===0,'Stage switch marked targets');check(m.fileStatus('a.py').status==='unread','File marked read');")
    def test_same_name_and_callsite_have_exact_source_identity(self):
        self.run_case("check(ReadingProgress.sourceURL(config,'run-a')==='https://example.invalid/fixture/blob/"+'1'*40+"/a.py#L2-L3','Wrong first source');check(ReadingProgress.sourceURL(config,'run-b').endsWith('/b.py#L2-L3'),'Same-name sources mixed');check(ReadingProgress.sourceURL(config,'caller').endsWith('/entry.py#L2-L2'),'Callsite expanded to full definition');check(ReadingProgress.sourceURL(config,'external')===null,'Unavailable source got a fake link');")
    def test_scope_completion_and_empty_scope_preserve_uncovered_definitions(self):
        self.run_case("m.checkGoal('input:one',true);check(m.fileStatus('a.py').status==='partial','One target claimed whole file');m.checkGoal('input:two',true);const a=m.fileStatus('a.py');check(a.status==='scope-complete' && a.total===2 && a.completed===2,'Scope completion wrong');check(a.uncovered.some(f=>f.symbol==='Worker.hidden'),'Excluded function disappeared');check(m.fileStatus('other.py').status==='out-of-scope','Empty target set counted complete');")
    def test_restore_requires_same_sha_range_and_depth(self):
        self.run_case("m.checkGoal('input:one',true);const saved=m.snapshot();const restored=ReadingProgress.create(config);restored.restore(saved);check(restored.snapshot().checks.length===1,'Valid self-check not restored');for(const change of [c=>c.revision='2'.repeat(40),c=>c.references['run-a'].line=1,c=>c.views[0].steps[0].depth='implementation']){const c=JSON.parse(JSON.stringify(config));change(c);if(c.revision!==config.revision)Object.values(c.references).forEach(r=>r.revision=c.revision);const n=ReadingProgress.create(c);n.restore(saved);check(n.snapshot().checks.length===0,'Changed source scope inherited old learning');}")
    def test_invalid_source_range_path_and_reference_are_rejected(self):
        self.run_case("for(const change of [c=>c.references['run-a'].line=0,c=>c.references['run-a'].path='../secret',c=>c.views[0].steps[0].callee='missing']){const c=JSON.parse(JSON.stringify(config));change(c);let rejected=false;try{ReadingProgress.create(c)}catch(e){rejected=true}check(rejected,'Broken source contract accepted');}")
    def test_exported_progress_key_not_navigation_id_controls_restore(self):
        self.run_case("config.views[0].steps[0].progressKey='exported-target-v1';const first=ReadingProgress.create(config);first.checkGoal('input:one',true);const saved=first.snapshot();check(saved.checks[0].progressKey==='exported-target-v1' && !('id' in saved.checks[0]),'Navigation ID used as persisted identity');config.views[0].steps[0].progressKey='changed-target-v2';const second=ReadingProgress.create(config);second.restore(saved);check(second.snapshot().checks.length===0,'Changed content target inherited old self-check');")

if __name__=='__main__':unittest.main()
