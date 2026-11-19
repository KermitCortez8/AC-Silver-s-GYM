import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import { chromium } from '../../../../.github/scripts/browser-tests/node_modules/playwright/index.mjs';
import { createServer } from '../../../../frontend/node_modules/vite/dist/node/index.js';
process.env.VITE_AUTH_API_BASE_URL='/api';
process.env.VITE_BACKEND_URL='http://127.0.0.1:8013';
process.env.VITE_SUPABASE_URL='';
process.env.VITE_SUPABASE_ANON_KEY='';
const qaOrigin='http://127.0.0.1:8013';
const webBase='http://127.0.0.1:5194';
const password='TC195-Synthetic-Only-2026!';
const readState=()=>fetch(qaOrigin+'/__qa/tc195', {
 headers: {'X-QA-Key': process.env.GYM_TEST_STRIPE_SHUTDOWN_KEY},
}).then(r=>r.json());
const login=async email=>{
 const r=await fetch(qaOrigin+'/api/auth/password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({correo:email,password})});
 assert.equal(r.status,200,'Acceso QA por API');
 return (await r.json()).token;
};
const api=async(method,path,token,data)=>{
 const r=await fetch(qaOrigin+path,{method,headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},...(data?{body:JSON.stringify(data)}:{})});
 return {status:r.status,body:await r.json()};
};
const out=process.env.GYM_TEST_STRIPE_ARTIFACTS;
const report = {
 case: 'TC-195',
 code: 'SG-RF23-IT01',
 title: 'Pago con tarjeta reserva stock y deja el pedido pendiente hasta confirmar en Stripe',
 provider: 'Stripe en modo de prueba',
 database: 'LocalGymService en memoria',
 steps: [],
};
const record=async(name,value)=>{
 report.steps.push({name,...value});
 await writeFile(out+'/resultado.json',JSON.stringify(report,null,2)+'\n');
 console.log(name,JSON.stringify(value));
};
const verifyCheckout=payment=>{
 const url=new URL(payment.checkout_url);
 assert.equal(url.origin,'https://checkout.stripe.com');
 assert.ok(payment.session_id.startsWith('cs_test_'),'sesión de prueba');
 return url.toString();
};
const waitForState=async(check,label)=>{
 for(let i=0;i<50;i++){
   const s=await readState();
   if(check(s)) return s;
   await new Promise(resolve=>setTimeout(resolve,500));
 }
 throw new Error(label);
};
let vite,browser,client;
try{
 const info=await readState();
 assert.equal(info.qa,true);
 assert.equal(info.stock,5);
 client=await login(info.customer);
 const admin=await login('admin@example.com');
 vite=await createServer({server:{host:'127.0.0.1',port:5194,strictPort:true,
  proxy:{'/api':qaOrigin}}});
 await vite.listen();
 browser=await chromium.launch();
 const page=await browser.newPage({locale:'es-PE'});
 await page.route('**/*',route=>{
   const url=new URL(route.request().url());
   return url.origin===webBase || /(^|\.)(stripe\.com|stripe\.network|stripecdn\.com|hcaptcha\.com|link\.com)$/.test(url.hostname)
    ?route.continue():route.abort();
 });
 await page.goto(webBase+'/login');
 await page.getByLabel('Correo',{exact:true}).fill(info.customer);
 await page.getByLabel('Contraseña',{exact:true}).fill(password);
 await page.getByRole('button',{name:'Entrar con correo',exact:true}).click();
 await page.waitForURL('**/user/dashboard');
 const items=[{id_producto:info.product,cantidad:2}];
 const open=await api('POST','/api/tienda/pedidos/checkout',client,{items});
 assert.equal(open.status,201,'Creación checkout QA');
 const first=open.body.pedido.id_pedido;
 const stripeUrl=verifyCheckout(open.body.payment);
 let s=await readState();
 assert.equal(s.stock,3);
 assert.deepEqual(s.orders.find(o=>o.id===first),{id:first,order:'PENDIENTE',payment:'PENDIENTE',total:35.4});
 await record('Reserva de dos unidades',{stock:3,pedido:'PENDIENTE',pago:'PENDIENTE',total:35.4});
 const refused=await api('PUT','/api/tienda/pedidos/'+first,admin,{estado_pedido:'CONFIRMADO'});
 assert.ok(refused.status>=400);
 assert.match(JSON.stringify(refused.body),/No se puede confirmar ni entregar un pedido sin pago confirmado/);
 assert.equal((await readState()).stock,3);
 await record('Intento de confirmación antes del pago',{http:refused.status,rechazado:true,stock:3});

 // Pausa el retorno automático para verificar que el primer cambio provenga del webhook real.
 await page.route('**/user/store/payment?result=success&**',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>Retorno de QA</title><p>Pago de prueba completado</p>'}),{times:1});
 await page.goto(stripeUrl,{waitUntil:'domcontentloaded'});
 let frame;
 for (let i=0;i<45&&!frame;i++){
   for (const candidate of page.frames()){
     if(await candidate.locator('[autocomplete=cc-number]').first().isVisible().catch(()=>false)){
       frame=candidate;
       break;
     }
   }
   if(!frame) await new Promise(r=>setTimeout(r,500));
 }
 assert.ok(frame,'Stripe debe cargar el formulario de tarjeta');
 // Completa el formulario oficial de Checkout con la tarjeta del sandbox.
 await frame.locator('[autocomplete=cc-number]').first().fill('4242424242424242');
 await frame.locator('[autocomplete=cc-exp]').first().fill('1230');
 await frame.locator('[autocomplete=cc-csc]').first().fill('123');
 await frame.locator('[autocomplete=cc-name]').first().fill('Cliente TC195 QA');
 const submit=frame.getByRole('button',{name:'Pagar',exact:true});
 await submit.click();
 await page.waitForURL(url=>url.origin===webBase&&url.searchParams.get('result')==='success',{timeout:35000});
 s=await waitForState(state=>state.events.includes('checkout.session.completed')&&state.orders.some(o=>o.id===first&&o.payment==='PAGADO'),
  'El webhook de checkout.session.completed no confirmó el pago');
 assert.deepEqual(s.orders.find(o=>o.id===first),{id:first,order:'PENDIENTE',payment:'PAGADO',total:35.4});
 assert.equal(s.stock,3);
 await record('Pago confirmado por webhook de Stripe',{evento:'checkout.session.completed',pedido:'PENDIENTE',pago:'PAGADO',stock:3});

 const secondOrder=await api('POST','/api/tienda/pedidos/checkout',client,{items});
 assert.equal(secondOrder.status,201);
 const second=secondOrder.body.pedido.id_pedido;
 assert.equal((await readState()).stock,1);
 await page.goto(verifyCheckout(secondOrder.body.payment),{waitUntil:'domcontentloaded'});
 await page.getByText('Atrás',{exact:true}).waitFor({timeout:18000});
 const cancelHref=page.locator('a[href*="result=cancel"]').filter({visible:true}).first();
 if(await cancelHref.count()) await cancelHref.click();
 else {
   const back=page.getByText('Atrás',{exact:true}).filter({visible:true}).first();
   assert.ok(await back.count(),'Checkout no mostró un control de cancelación accesible');
   await back.click();
 }
 await page.waitForURL(url=>url.origin===webBase && url.pathname==='/user/store/payment',{timeout:25000});
 await page.getByText('Cancelaste el pago y restauramos tu carrito.').waitFor({timeout:20000});
 s=await waitForState(state=>state.orders.some(o=>o.id===second && o.order==='CANCELADO'),'El pedido cancelado no se guardó');
 assert.equal(s.stock,3);
 assert.equal(s.orders.find(o=>o.id===first).payment,'PAGADO');
 assert.equal(s.orders.find(o=>o.id===second).payment,'PENDIENTE');
 await page.screenshot({path:out+'/carrito-restaurado.png',fullPage:true,animations:'disabled'});
 await record('Cancelación en Stripe y carrito restaurado',{pedido:'CANCELADO',stockDuranteReserva:1,stockRestaurado:3,carrito:true});
 report.result='passed';
 await writeFile(out+'/resultado.json',JSON.stringify(report,null,2)+'\n');
} catch (error) {
  report.result = 'failed';
  await writeFile(out + '/resultado.json', JSON.stringify(report, null, 2) + '\n');
  const safe = String(error.message)
    .replace(/https:\/\/checkout\.stripe\.com\/[^\s"']+/g, '[Checkout de prueba]')
    .replace(/(?:cs_test_|pi_|whsec_|sk_test_)[A-Za-z0-9_-]+/g, '[identificador]');
  console.error(safe);
  process.exitCode = 1;
} finally {
  if (client) {
    const remaining = await readState().catch(() => ({orders: []}));
    for (const order of remaining.orders.filter(o => o.order === 'PENDIENTE' && o.payment === 'PENDIENTE')) {
      await api('POST', '/api/tienda/pedidos/' + order.id + '/cancelar-pago', client).catch(() => {});
    }
  }
 await browser?.close();
 await vite?.close();
}
