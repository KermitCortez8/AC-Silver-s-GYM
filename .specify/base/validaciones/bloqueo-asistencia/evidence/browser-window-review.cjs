// Revisión visual con API y sesión sintéticas. No consulta ni modifica Supabase.
const {chromium}=require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-visual/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base=process.env.GYM_REVIEW_URL || 'http://127.0.0.1:5173';
const admin={id:'SGADM-VISUAL',id_usuario:'SGADM-VISUAL',role:'admin',name:'Prueba visual',email:'visual@example.com'};
const schedule={id_horario_servicio:1,servicio:'fitness',dia:'lunes',hora_inicio:'10:00',hora_fin:'12:00',activo:true,cupos:10,matriculados:1,rutina_nombre:'Clase de prueba'};
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const results=[];
 try{
  for(const scenario of [{kind:'otra-semana',width:1440},{kind:'clase-terminada',width:390},{kind:'margen-30min',width:1440},{kind:'general-fuera30',width:390}]){
   const context=await browser.newContext({viewport:{width:scenario.width,height:950}});
   await context.addInitScript(({admin,width})=>{localStorage.setItem('gym_auth_user',JSON.stringify(admin));localStorage.setItem('gym_auth_token','sesion-visual-simulada');localStorage.setItem('gym_auth_token_expiry',String(Date.now()+3600000));localStorage.setItem('ac-silver-theme',width===390?'dark':'light');},{admin,width:scenario.width});
   const pending={id_asistencia:1,tipo:'general',servicio:'gimnasio',estado:'dentro',fecha:'2026-11-09',hora_entrada:'09:00:00',hora_salida:''};
   const conflict='El cliente tiene una entrada sin salida en la asistencia general. Registra la salida de esa asistencia antes de registrar otra entrada.';
   const reason=scenario.kind==='margen-30min'?'La entrada se habilita de 10:00 a 12:00 (hora de Perú).':scenario.kind==='otra-semana'?'La entrada se habilita el día de esta sesión (hora de Perú).':'La hora de esta clase ya pasó. No se puede registrar la asistencia.';
   let writes=0;
   await context.route('**/*',route=>new URL(route.request().url()).origin===new URL(base).origin?route.fallback():route.abort());
   await context.route('**/api/**',async route=>{
    const req=route.request(),url=new URL(req.url());
    if(req.method()!=='GET'){writes++;return route.fulfill({status:409,json:{detail:'No hay escrituras autorizadas en esta revisión visual'}});}
    if(url.pathname==='/api/auth/me')return route.fulfill({json:admin});
    if(url.pathname==='/api/asistencia/horarios')return route.fulfill({json:{fecha:'2026-11-09',horarios:[schedule]}});
    if(url.pathname==='/api/asistencia/resumen')return route.fulfill({json:{fecha:'2026-11-09',entradas:1,salidas:0,dentro:1,capacidad:30,disponibles:29,pendientes:[],recientes:[]}});
    if(url.pathname==='/api/asistencia/cliente')return route.fulfill({json:{cliente:{nombre:'Cliente de prueba',dni:'12345678',estado:'ACTIVO',plan:'MENSUAL'},membresia:{fecha_fin:'2026-12-09'},horarios:[],general:{puede_entrar:false,motivo:conflict,coincidencia_horario:false,asistencia_abierta:{...pending,tipo:'horario',servicio:'fitness'}}}});
    if(url.pathname==='/api/asistencia/horarios/1/clientes')return route.fulfill({json:{fecha:url.searchParams.get('fecha'),horario:schedule,clientes:[{id_matricula:7,cliente:{id_cliente:999,nombre:'Cliente de prueba',dni:'12345678'},asistencia:null,asistencia_abierta:scenario.kind==='margen-30min'?pending:null,motivo_coincidencia:scenario.kind==='margen-30min'?conflict:'',puede_entrar:false,motivo:reason}]}});
    return route.fulfill({json:[]});
   });
   const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(`${base}/admin/attendance`);
   if(scenario.kind==='general-fuera30'){
    await page.getByRole('tab',{name:'Gimnasio general',exact:true}).click();
    await page.getByLabel('DNI del cliente',{exact:true}).fill('12345678');
    await page.getByText('Entrada en asistencia por horarios',{exact:true}).waitFor();
    assert.equal(await page.locator('.att-general-visit [role=alert]').count(),0);
    assert.equal(await page.locator('.att-general-visit').getByRole('button',{name:'Registrar salida',exact:true}).isVisible(),true);
   }else{
   if(scenario.kind==='otra-semana')await page.getByRole('navigation',{name:'Semanas del mes'}).getByRole('button',{name:/Semana 4/}).click();
   await page.getByRole('button',{name:/Clase de prueba/}).first().click();
   await page.getByText(reason,{exact:true}).waitFor();
   assert.equal(await page.getByRole('button',{name:'Registrar salida pendiente de Cliente de prueba',exact:true}).count(),scenario.kind==='margen-30min'?1:0);
   if(scenario.kind==='margen-30min')await page.getByText(conflict,{exact:true}).waitFor();
   assert.equal(await page.getByRole('button',{name:'Registrar entrada de Cliente de prueba',exact:true}).isDisabled(),true);
   }
   await page.evaluate(()=>scrollTo(0,0));const file=scenario.kind==='margen-30min'?'aviso-margen-30min.png':`sin-aviso-${scenario.kind}.png`;
   await page.screenshot({path:path.join(__dirname,file),fullPage:true});assert.equal(writes,0);assert.deepEqual(errors,[]);
   results.push({...scenario,aviso_cruzado:scenario.kind==='margen-30min',escrituras:writes,errores:errors,captura:file});await context.close();
  }
  fs.writeFileSync(path.join(__dirname,'browser-window-results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exit(1)});
