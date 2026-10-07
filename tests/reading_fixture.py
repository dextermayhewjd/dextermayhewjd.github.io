"""Synthetic learning-pack v1. These snippets are not slime source material."""
import hashlib

REVISION = '1' * 40

def pack():
    files = {
        'entry.py': 'def generate(task):\n    return Worker().run(task)\n',
        'a.py': 'class Worker:\n    def run(self, task):\n        return task\n\n    def hidden(self):\n        return None\n',
        'b.py': 'class Worker:\n    def run(self, task):\n        return str(task)\n',
        'other.py': 'def unused():\n    return None\n',
    }
    functions = {
        'entry.py': [('generate', 1, 2)],
        'a.py': [('Worker.run', 2, 3), ('Worker.hidden', 5, 6)],
        'b.py': [('Worker.run', 2, 3)],
        'other.py': [('unused', 1, 2)],
    }
    metadata = {path: {
        'text': text, 'totalLines': len(text.splitlines()),
        'blobSha256': hashlib.sha256(text.encode()).hexdigest(),
        'functions': [dict(symbol=s, line=a, endLine=b) for s,a,b in functions[path]],
    } for path,text in files.items()}
    references = {}
    for key,path,symbol,line,end in [
        ('caller', 'entry.py', 'generate', 2, 2),
        ('run-a', 'a.py', 'Worker.run', 2, 3),
        ('run-b', 'b.py', 'Worker.run', 2, 3),
    ]:
        references[key] = dict(available=True, revision=REVISION, path=path,
            symbol=symbol, line=line, endLine=end, blobSha256=metadata[path]['blobSha256'],
            text='\n'.join(files[path].splitlines()[line-1:end]), label=symbol)
    references['external'] = dict(available=False, revision=REVISION,
        label='External.run', reason='测试边界：外部实现不可获取')
    def step(id, label, callee):
        return dict(id=id, label=label, kind='call', depth='trace',
            summary='交互夹具，不是 slime 的真实任务流程。', inputs=['task'],
            returns={'type':'object','fields':['result']}, effect='返回示意结果',
            condition='仅测试界面', caller='caller', callee=callee,
            files=['entry.py', references[callee]['path']])
    return dict(schemaVersion=1, fixture=True, chapterId='reading-fixture',
        title='跨文件阅读器测试夹具', repository='https://example.invalid/fixture',
        revision=REVISION, generatedAt='2026-10-07', files=metadata, references=references,
        inventory=[dict(path=p, category='python', group='fixture', inChapter=p!='other.py') for p in files],
        views=[
            dict(id='input', label='测试阶段：输入', description='合成夹具',
                 steps=[step('one','追踪输入合同','run-a'),step('two','追踪返回合同','run-a')]),
            dict(id='execution', label='测试阶段：执行', description='合成夹具',
                 steps=[step('three','追踪另一个同名方法','run-b')]),
        ])
