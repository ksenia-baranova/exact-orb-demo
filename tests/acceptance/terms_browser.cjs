// TASK-T-02 browser checks. Production HTML/CSS/modules are served unchanged.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require('playwright');
const { createHash } = require('node:crypto');
const root = path.resolve(__dirname,'../..');
const [scenario, output] = process.argv.slice(2);
const ui = path.join(root,'src/exact_orb/http_api/ui');
const views = JSON.parse(fs.readFileSync(path.join(root,'tests/http_api/golden/session_view.json')));
const charts = JSON.parse(fs.readFileSync(path.join(root,'tests/http_api/golden/chart_dto.json')));
const normalize = text => text.replace(/\s+/gu,' ').trim();
let examples = 0;
const evidence = [];
const server = http.createServer((req,res) => {
  const name = req.url === '/' ? 'index.html' : req.url.replace(/^\/ui\//,'');
  if (!/^[a-z_]+\.(html|css|mjs)$/.test(name)) { res.writeHead(404); res.end(); return; }
  const file = path.join(ui,name);
  if (!fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type',name.endsWith('.mjs') ? 'text/javascript' : name.endsWith('.css') ? 'text/css' : 'text/html');
  res.end(fs.readFileSync(file));
});
function oracle() {
  const draft = fs.readFileSync(path.join(root,'docs/project_management/changes/terms-of-use/terms_draft.md'),'utf8').replace(/\r\n/g,'\n');
  const q = draft.split('## Текст для страницы после утверждения Owner\n')[1].split('## Сверка Analyst')[0].trim()+'\n';
  assert.equal(createHash('sha256').update(q).digest('hex'),'ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0');
  return normalize(q.split('\n').filter(line => !/^\|\s*---/.test(line)).join('\n')
    .replace(/^### /gm,'').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/\*\*/g,'').replace(/\|/g,' '));
}
(async () => {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const url = 'http://127.0.0.1:'+server.address().port;
  const browser = await chromium.launch({channel:process.env.TERMS_BROWSER_CHANNEL || 'chrome',headless:true});
  try {
    const context = await browser.newContext({viewport:{width:360,height:740},serviceWorkers:'block'});
    async function fresh(saved=false) {
      const page = await context.newPage(), requests=[];
      await page.route('**/*',async route => {
        const r=route.request(), p=new URL(r.url()).pathname;
        if (!['/session/bootstrap','/charts/current','/charts/natal','/places'].includes(p)) return route.continue();
        requests.push({path:p,method:r.method(),body:r.postDataJSON()});
        const body = p === '/session/bootstrap' ? {status:'ready',state_version:1}
          : p === '/charts/current' ? (saved ? {...views.known_ready,chart:charts.natal} : views.empty)
          : p === '/places' ? {items:[{place_id:'524901',display_name:'Москва',admin1_name:'Москва',country_code:'RU'}]}
          : {status:'chart_ready',state_version:2,chart:charts.natal};
        await route.fulfill({json:body,headers:{'X-Request-ID':'tester-leaf'}});
      });
      await page.goto(url);
      await page.waitForFunction(() => document.querySelector('#session-status')?.textContent.includes('Сохранённой карты пока нет.')
        || document.querySelector('#session-status')?.textContent.includes('Карта доступна.'));
      if (saved) await page.getByRole('button',{name:'Изменить данные',exact:true}).click();
      return {page,requests};
    }
    const posts = requests => requests.filter(r => r.path === '/charts/natal');
    async function focusVisible(page, area) {
      assert.equal(await page.evaluate(id => {
        const active=document.activeElement, box=active.getBoundingClientRect(), style=getComputedStyle(active);
        return !!document.getElementById(id).contains(active) && box.width>0 && box.height>0
          && active.matches(':focus-visible') && style.outlineStyle !== 'none' && parseFloat(style.outlineWidth)>0;
      },area),true,'visible keyboard focus in '+area);
    }
    async function tabTo(page,id,reverse=false) {
      for (let n=0;n<30;n++) {
        if (await page.evaluate(id => document.activeElement.id===id,id)) return;
        await page.keyboard.press(reverse?'Shift+Tab':'Tab');
      }
      assert.fail('Tab did not reach '+id);
    }
    if (scenario === 'presentation') {
      // Given открыта форма и видно пояснение неизвестного времени
      const {page,requests}=await fresh();
      const before=await page.evaluate(() => {
        const link=document.getElementById('terms-link'), label=document.querySelector('[for="terms-acknowledged"]');
        const font=node => ['fontFamily','fontSize','fontStyle','fontWeight'].map(k => getComputedStyle(node)[k]);
        return {name:link.textContent,font:font(link),hint:font(document.querySelector('[for="time-unknown"] small')),
          below:link.getBoundingClientRect().top>=label.getBoundingClientRect().bottom};
      });
      // When пользователь находит ссылку условий под отметкой ознакомления
      assert.equal(before.name,'Условия использования сервиса'); assert.deepEqual(before.font,before.hint); assert.equal(before.below,true);
      await page.getByRole('link',{name:'Условия использования сервиса',exact:true}).click();
      // Then видимый текст совпадает с утверждённой редакцией и содержит обязательные сведения
      const actual=normalize(await page.locator('#terms-content').innerText()), expected=oracle();
      assert.equal(actual,process.env.TERMS_BAD_ORACLE ? expected.replace('exact_orb@mail.ru','wrong@mail.ru') : expected);
      assert.deepEqual(await page.locator('#terms-content a').evaluateAll(nodes => nodes.map(n=>n.href)),
        ['mailto:exact_orb@mail.ru','https://github.com/ksenia-baranova/exact-orb-demo']);
      assert.equal(posts(requests).length,0);
      evidence.push({font:before.font,approvedText:true,hrefs:['mailto:exact_orb@mail.ru','https://github.com/ksenia-baranova/exact-orb-demo']});
      await page.screenshot({path:path.join(output,'terms-mobile.png'),fullPage:true});
      await page.close(); examples++;
    } else if (scenario === 'keyboard') {
      for (const width of [359,360,361,768,1440]) for (const action of ['agree','back']) for (const checked of [false,true]) {
        // Given форма доступна с клавиатуры и указатель не используется
        const {page,requests}=await fresh(); await page.setViewportSize({width,height:740});
        await tabTo(page,'terms-acknowledged'); if (checked) await page.keyboard.press('Space');
        await page.keyboard.press('Tab'); assert.equal(await page.locator('#terms-link').evaluate(n=>n===document.activeElement),true);
        // When пользователь фокусирует ссылку и выполняет переход с каждым возвратом в отдельном проходе
        await focusVisible(page,'birth-page'); await page.keyboard.press('Enter'); await focusVisible(page,'terms-page');
        const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
        assert.equal(overflow,0,'width '+width);
        await tabTo(page,'terms-agree'); await focusVisible(page,'terms-page');
        await page.keyboard.press('Tab'); assert.equal(await page.locator('#terms-back').evaluate(n=>n===document.activeElement),true);
        await page.keyboard.press('Shift+Tab'); assert.equal(await page.locator('#terms-agree').evaluate(n=>n===document.activeElement),true);
        if (action==='back') await page.keyboard.press('Tab');
        const names=await page.locator('#terms-'+action).innerText(); assert.equal(names,action==='agree'?'Согласен':'Вернуться к форме');
        await page.keyboard.press(action==='agree'?'Space':'Enter');
        // Then доступны названия действий и focus остаётся на видимом содержимом
        await focusVisible(page,'birth-page'); assert.equal(await page.locator('#terms-acknowledged').isChecked(),action==='agree'||checked);
        assert.equal(posts(requests).length,0); evidence.push({width,action,checked,overflow});
        if(width===360 && !checked) await page.screenshot({path:path.join(output,'keyboard-'+action+'.png')});
        await page.close(); examples++;
      }
    } else if (scenario === 'targets') {
      const {page,requests}=await fresh();
      // Given на viewport 360 px измеритель проверен на позитивных и негативных контролях
      async function measure(id) {
        await page.locator('#'+id).evaluate(node => node.scrollIntoView({block:'center',inline:'center',behavior:'instant'}));
        return page.evaluate(id => {
          const target=document.getElementById(id), b=target.getBoundingClientRect();
          const r={x:b.x+(b.width-44)/2,y:b.y+(b.height-44)/2,width:44,height:44};
          let misses=0;
          const probes=[.01,43.99,...Array.from({length:44},(_,i)=>i+.5)];
          for(const x of probes)for(const y of probes) {
            const hit=document.elementFromPoint(r.x+x,r.y+y);
            if(!hit || !(hit===target||target.contains(hit))) misses++;
          }
          return {id,bbox:{width:b.width,height:b.height},r,misses,pass:b.width>=44&&b.height>=44&&misses===0};
        },id);
      }
      await page.evaluate(() => {
        const host=document.createElement('div'); host.id='tester-controls';
        host.style.cssText='position:fixed;left:0;top:0;z-index:99999;width:300px;height:100px;background:white';
        for(const [id,w,h,x] of [['positive',44,44,0],['short-x',43,44,50],['short-y',44,43,100],['overlay',44,44,150],['clipped',44,44,200]]) {
          const clip=document.createElement('div'); clip.style.cssText=`position:absolute;left:${x}px;top:10px;width:${id==='clipped'?43:44}px;height:44px;overflow:hidden`;
          const t=document.createElement('button'); t.id=id;t.type='button';t.textContent=id;
          t.style.cssText=`box-sizing:border-box;padding:0;border:0;border-radius:0;min-height:0;min-width:0;width:${w}px;height:${h}px`;
          clip.append(t);host.append(clip);
          if(id==='overlay'){const cover=document.createElement('button');cover.id='cover';cover.style.cssText='position:absolute;left:170px;top:10px;width:3px;height:44px;padding:0;border:0;min-height:0';host.append(cover);}
        }
        document.body.append(host); window.testerClicks=[];
        document.addEventListener('click',e=>window.testerClicks.push({id:e.target.id,trusted:e.isTrusted}),true);
      });
      for(const id of ['positive','short-x','short-y','overlay','clipped']) {
        const measured=await measure(id); assert.equal(measured.pass,id==='positive',id); evidence.push(measured);
      }
      await page.mouse.click(22,32); assert.deepEqual(await page.evaluate(()=>window.testerClicks.at(-1)),{id:'positive',trusted:true});
      await page.mouse.click(171,32); assert.deepEqual(await page.evaluate(()=>window.testerClicks.at(-1)),{id:'cover',trusted:true});
      await page.locator('#tester-controls').evaluate(n=>n.remove());
      // When доверенный указатель активирует область ссылки и каждого возврата
      const points=[[.01,.01],[43.99,.01],[.01,43.99],[43.99,43.99],[22,.01],[22,43.99],[.01,22],[43.99,22],[22,22]];
      for(const id of ['terms-link','terms-agree','terms-back']) for(const [x,y] of points) {
        const termsVisible=await page.locator('#terms-page').isVisible();
        if(id!=='terms-link'&&!termsVisible) await page.locator('#terms-link').click();
        if(id==='terms-link'&&termsVisible) await page.locator('#terms-back').click();
        if(id==='terms-back') {await page.locator('#terms-back').click();await page.locator('#terms-acknowledged').uncheck();await page.locator('#terms-link').click();}
        const measured=await measure(id); assert.equal(measured.pass,true,JSON.stringify(measured)); evidence.push({...measured,probe:[x,y]});
        await page.mouse.click(measured.r.x+x,measured.r.y+y);
        // Then фактический получатель и срабатывание подтверждают доступную область нужного размера
        assert.deepEqual(await page.evaluate(()=>window.testerClicks.at(-1)),{id,trusted:true});
        assert.equal(await page.locator('#terms-page').isVisible(),id==='terms-link');
        if(id!=='terms-link')assert.equal(await page.locator('#terms-acknowledged').isChecked(),id==='terms-agree');
        examples++;
      }
      assert.equal(posts(requests).length,0); await page.close();
    } else if (scenario === 'builds') {
      for(const method of ['manual','page'])for(const value of ['00:00','14:30','23:59',null,'','-00:01','24:00','12:6','date','place']) {
        const {page,requests}=await fresh();await page.clock.install();
        await page.locator('#birth-date').fill('1990-09-02');
        await page.locator('#birth-place').fill('Моск');await page.clock.fastForward(300);
        await page.getByRole('option').first().click();await page.locator('#birth-time').fill('14:30');
        const valid=['00:00','14:30','23:59',null].includes(value);
        if(value===null)await page.locator('#time-unknown').check();
        else if(value==='date')await page.locator('#birth-date').fill('');
        else if(value==='place')await page.locator('#birth-place').fill('Москва');
        else {await page.locator('#birth-time').fill('');await page.locator('#birth-time').pressSequentially(value);}
        const raw=await page.locator('#birth-time').inputValue();
        if(method==='manual') {
          await page.locator('#terms-acknowledged').check();await page.locator('#terms-acknowledged').uncheck();
          assert.equal(await page.locator('#terms-page').isVisible(),false);assert.equal(posts(requests).length,0);
          await page.locator('#terms-acknowledged').check();
        } else {await page.locator('#terms-link').click();await page.locator('#terms-agree').click();}
        assert.equal(posts(requests).length,0);
        await page.locator('button[type=submit]').click();
        if(valid) {
          await page.waitForFunction(()=>document.querySelector('#session-status').textContent.includes('Карта доступна.'));
          assert.equal(posts(requests).length,1);
          assert.deepEqual(posts(requests)[0].body,{birth_date:'1990-09-02',birth_time:value,place_id:'524901'});
        }else{
          assert.equal(posts(requests).length,0);
          assert.equal(await page.locator('#'+(value==='date'?'date':value==='place'?'place':'time')+'-error').isVisible(),true);
        }
        assert.equal(await page.locator('#birth-time').inputValue(),raw);
        evidence.push({method,input:value,nativeTime:raw,posts:posts(requests).length});
        examples++;await page.close();
      }
    } else if (scenario === 'reload') {
      for(const saved of [false,true])for(const method of ['none','manual','page'])for(const mode of ['reload','reopen']) {
        // Given пользователь выбрал checkbox и до загрузки увидел выбранное состояние
        let {page,requests}=await fresh(saved);
        if(method==='manual')await page.locator('#terms-acknowledged').check();
        if(method==='page'){await page.locator('#terms-link').click();await page.locator('#terms-agree').click();}
        assert.equal(await page.locator('#terms-acknowledged').isChecked(),method!=='none');
        // When пользователь выполняет новую загрузку формы способом из примера
        if(mode==='reload') {
          await page.reload();await page.waitForFunction(()=>document.querySelector('#session-status')?.textContent.includes('карты пока нет.')||document.querySelector('#session-status')?.textContent.includes('Карта доступна.'));
          if(saved)await page.getByRole('button',{name:'Изменить данные',exact:true}).click();
        }else{await page.close();({page,requests}=await fresh(saved));}
        // Then подтверждение прошлого посещения не восстановлено
        assert.equal(await page.locator('#terms-acknowledged').isChecked(),false);
        await page.locator('button[type=submit]').click(); assert.equal(posts(requests).length,0);
        assert.equal(await page.locator('#acknowledged-error').isVisible(),true);
        evidence.push({saved,method,mode,checked:false});await page.close();examples++;
      }
    } else throw new Error('unknown scenario '+scenario);
    fs.writeFileSync(path.join(output,scenario+'.json'),JSON.stringify({scenario,examples,browser:browser.version(),evidence},null,2));
    console.log(JSON.stringify({scenario,examples,status:'PASS',browser:browser.version()}));
    await context.close();
  } finally {await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
