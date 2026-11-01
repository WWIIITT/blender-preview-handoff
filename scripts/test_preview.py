"""Isolated smoke tests: python3 test_preview.py. No production side effects."""
import json,tempfile,threading,urllib.request,urllib.error
from pathlib import Path
from functools import partial
import preview as m
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
with tempfile.TemporaryDirectory() as td:
 root=Path(td);(root/'中文 文本.txt').write_text('<script>alert(1)</script> & 内容');(root/'clip.bin').write_bytes(bytes(range(256)))
 data={'title':'test <b>','version':'v1','items':[{'id':'text','kind':'text','path':'中文 文本.txt'},{'id':'clip','kind':'file','path':'clip.bin'}]};src=root/'manifest.json';src.write_text(json.dumps(data));out=root/'preview';m.build(src,out)
 assert '&lt;script&gt;alert' in (out/'index.html').read_text()
 try:m.build(src,out);raise AssertionError('overwritten')
 except ValueError:pass
 data['items'][1]['path']='missing';src.write_text(json.dumps(data))
 try:m.build(src,root/'bad');raise AssertionError('missing accepted')
 except ValueError:assert not (root/'bad').exists()
 server=m.ThreadingHTTPServer(('127.0.0.1',0),partial(m.PreviewHandler,directory=str(out)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
 try:
  assert opener.open(url+'/').status==200
  for r,expected in [('bytes=10-19',bytes(range(10,20))),('bytes=-5',bytes(range(251,256))),('bytes=250-',bytes(range(250,256)))]:
   response=opener.open(urllib.request.Request(url+'/media/clip.bin',headers={'Range':r}));assert response.status==206 and response.read()==expected
  response=opener.open(urllib.request.Request(url+'/media/clip.bin',method='HEAD'));assert response.headers['Content-Length']=='256' and response.read()==b''
  (out/'escape').symlink_to(root/'clip.bin')
  for path,h,code in [('/media/clip.bin',{'Range':'bytes=999-'},416),('/missing',{},404),('/media/',{},404),('/escape',{},403)]:
   try:opener.open(urllib.request.Request(url+path,headers=h));raise AssertionError(path)
   except urllib.error.HTTPError as e:assert e.code==code
 finally:server.shutdown();server.server_close()
print('PASS: escaping, paths, overwrite protection, HTTP, HEAD, Range, 416, 404, root boundary')
