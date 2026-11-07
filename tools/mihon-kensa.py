# 見本サイトを出す前に pages-dist の全部の頁を見る：空欄〔…〕が残っていないか・頁が貼っている画像や動画が手元に在るか（11/04 ai-cm が作りかけのまま公開されていた）
# 使い方: python3 mihon-kensa.py [pages-dist の場所]  → 1件でも 🔴 なら終了コード 1
import os,re,sys
root=sys.argv[1] if len(sys.argv)>1 else 'pages-dist'
ng=0;n=0
for d,_,fs in os.walk(root):
  for f in fs:
    if not f.endswith('.html'):continue
    p=os.path.join(d,f);t=open(p,encoding='utf-8').read();n+=1
    for m in re.findall(r'〔[^〕]{0,30}〕',t):ng+=1;print('🔴 空欄',os.path.relpath(p,root),m)
    for s in re.findall(r'(?:src|href)="([^"#?]+)"',t):
      if re.match(r'(https?:|mailto:|tel:|data:|/)',s) or s.endswith('/'):continue
      if not os.path.exists(os.path.join(d,s)):ng+=1;print('🔴 無い',os.path.relpath(p,root),s)
print(f'頁 {n} ／ 🔴 {ng}');sys.exit(1 if ng else 0)
