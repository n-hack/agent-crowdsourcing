// チラシ・パンフの HTML を印刷の大きさの JPG と PDF に書き出し、依頼の記載項目が全部入っているか・下の帯と重なっていないかを確かめる
// 使い方: node chirashi-kakidasu.cjs <flyer.html> <幅mm> <高さmm> [記載項目.txt（1行1項目）]
//   HTML の決まり: 1面ごとに <div class="page">、下の連絡先の帯は class="ft"（重なりの確かめに使う）
//   出る物: 同じ場所に men1.jpg・men2.jpg …（約300dpi）と flyer.pdf
//   止まる時: 記載項目が1つでも無い／帯と重なっている → 終了コード 1（出す前に直す）
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');const fs=require('fs');const path=require('path');
const [html,wmm,hmm,kou]=process.argv.slice(2);
if(!html||!wmm||!hmm){console.log('使い方: node chirashi-kakidasu.cjs <flyer.html> <幅mm> <高さmm> [記載項目.txt]');process.exit(2)}
const dir=path.dirname(path.resolve(html));const W=+wmm,H=+hmm;const px=mm=>Math.round(mm/25.4*96);const scale=(W/25.4*300)/px(W);
(async()=>{const b=await chromium.launch();let ng=0;try{
const p=await b.newPage({viewport:{width:px(W),height:px(H)},deviceScaleFactor:scale});
await p.goto('file://'+path.resolve(html));await p.waitForTimeout(800);
const pages=await p.$$('.page');if(!pages.length){console.log('🔴 class="page" が1つも無い');process.exit(1)}
for(let i=0;i<pages.length;i++){const f=path.join(dir,`men${i+1}.jpg`);await pages[i].screenshot({path:f,type:'jpeg',quality:95});console.log('書いた',f)}
await p.pdf({path:path.join(dir,'flyer.pdf'),width:W+'mm',height:H+'mm',printBackground:true});
// 帯との重なり・はみ出し（mm）
const r=await p.evaluate(()=>[...document.querySelectorAll('.page')].map((pg,i)=>{const ft=pg.querySelector('.ft');const P=pg.getBoundingClientRect();const mm=v=>+(v/3.7795).toFixed(1);
 let low=0;for(const e of pg.children){if(e===ft)continue;const q=e.getBoundingClientRect();if(ft&&q.bottom>ft.getBoundingClientRect().top+.5&&q.top<ft.getBoundingClientRect().top)low++}
 let out=0;for(const e of pg.querySelectorAll('*')){const q=e.getBoundingClientRect();if(q.width&&(q.bottom>P.bottom+.5||q.right>P.right+.5))out++}
 return {men:i+1,obi_kasanari:low,hamidashi:out}}));
for(const x of r){const ok=!x.obi_kasanari&&!x.hamidashi;if(!ok)ng++;console.log(ok?'✅':'🔴',`${x.men}面 帯と重なる ${x.obi_kasanari}／紙の外へ出る ${x.hamidashi}`)}
if(kou){const t=(await p.evaluate(()=>document.body.innerText)).replace(/\s/g,'');for(const w of fs.readFileSync(kou,'utf8').split('\n').map(s=>s.trim()).filter(Boolean)){const has=t.includes(w.replace(/\s/g,''));if(!has)ng++;console.log(has?'✅':'🔴',w)}}
}finally{await b.close()}console.log(ng?`🔴 ${ng}件 直してから出す`:'✅ 全部そろった');process.exit(ng?1:0)})();
