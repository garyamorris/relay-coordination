const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.BASE_URL||'http://127.0.0.1:8000');await page.waitForSelector('#identity option[value="maya"]',{state:'attached'});
 await page.getByRole('button',{name:'＋ New discussion'}).click();
 const title='Browser acceptance '+Date.now();await page.locator('#discussion-title').fill(title);
 await page.getByRole('button',{name:'Analyse discussion →'}).click();
 await page.waitForSelector('#question-0');assert.equal(await page.locator('.consultation').count(),4);
 await page.locator('#question-0').fill('Please confirm access-control evidence and the accountable reviewer.');
 await page.getByRole('button',{name:'Approve selected & send →'}).click();await page.waitForFunction(()=>!document.querySelector('#question-0'));
 for(const id of ['sam','finn','alex','olivia']){
  await page.locator('#identity').selectOption(id);
  await page.waitForFunction(()=>document.querySelector('#detail .reply-form'));
  const form=page.locator('#detail .reply-form');await form.locator('[name=text]').fill(id==='sam'?'Access evidence is incomplete.':'Advisory support pending completion of assigned action.');
  await form.locator('[name=stance]').selectOption(id==='sam'?'concern':'support');await form.locator('[name=action]').fill('Confirm department readiness');await form.locator('[name=owner]').fill(id);await form.locator('[name=due]').fill('2026-12-01');
  await form.getByRole('button',{name:'Submit department response →'}).click();await page.getByRole('heading',{name:'Your response is recorded'}).waitFor();
 }
 await page.locator('#identity').selectOption('maya');await page.getByRole('heading',{name:'Shared decision brief'}).waitFor();
 await page.getByRole('heading',{name:'Conflicting input'}).waitFor();assert.match(await page.locator('#detail').innerText(),/4 department response\(s\) recorded; 0 outstanding/);
 await page.screenshot({path:'artifacts/desktop.png',fullPage:true});await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:'artifacts/mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log(JSON.stringify({passed:true,scenario:title,checks:['create','edit','approve','four identity replies','conflict synthesis','desktop','mobile no overflow','no browser errors']}));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
