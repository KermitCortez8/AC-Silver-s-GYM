const { chromium } = require('playwright');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}),
    args: ['--no-sandbox'],
  });
  try {
    const page = await browser.newPage();
    await page.goto(process.env.PROTOTYPE_REPORT_URL || 'http://127.0.0.1:8768/prototipos/laminas.html', { waitUntil: 'networkidle' });
    await page.evaluate(() => Promise.all(Array.from(document.images).map(img => img.decode())));
    await page.pdf({ path: path.join(__dirname, 'Specs-y-prototipos-chatbot.pdf'), preferCSSPageSize: true, printBackground: true });
    console.log('PDF exportado con ECU y capturas reales del prototipo.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
