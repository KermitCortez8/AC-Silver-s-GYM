// JUnit y manifiesto de capturas de la misma ejecución, sin tokens ni peticiones.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';

const xml = value => String(value ?? '').replace(/[<>&"']/g, char => ({
  '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;',
})[char]).replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, '');

export default class EvidenceReporter {
  cases = [];
  onBegin(config) {
    this.testDir = config.rootDir;
    this.directory = process.env.GYM_BROWSER_REPORT_DIR;
    fs.mkdirSync(path.join(this.directory, 'evidence/browser'), { recursive: true });
  }
  onTestEnd(test, result) {
    const classname = path.relative(this.testDir, test.location.file).replaceAll('\\', '/');
    const titles = test.titlePath().map(title => title.replaceAll('\\', '/'));
    const fileIndex = titles.findIndex(title => title === classname || title.endsWith(`/${classname}`));
    const name = fileIndex < 0 ? test.title : titles.slice(fileIndex + 1).join(' / ');
    const description = test.annotations.find(a => a.type === 'descripcion')?.description || test.title;
    const expected = test.annotations.find(a => a.type === 'esperado')?.description || '';
    const steps = [];
    const visit = entries => entries.forEach(step => {
      if (step.category === 'test.step') steps.push(`${step.error ? 'FALLÓ' : 'EJECUTADO'}: ${step.title}`);
      visit(step.steps || []);
    });
    visit(result.steps);
    const files = [];
    for (const attachment of result.attachments) {
      if (attachment.contentType !== 'image/png' || !attachment.path) continue;
      const data = fs.readFileSync(attachment.path);
      const sha256 = createHash('sha256').update(data).digest('hex');
      const relative = `evidence/browser/${sha256}.png`;
      fs.writeFileSync(path.join(this.directory, relative), data);
      files.push({ path: relative, sha256, title: attachment.name });
    }
    this.cases.push({ classname, name, description, expected, steps, files,
      status: result.status, duration: result.duration / 1000,
      error: result.error?.message || '' });
  }
  onEnd() {
    fs.writeFileSync(path.join(this.directory, 'browser.evidence.json'), JSON.stringify({
      version: 1, cases: this.cases,
    }, null, 2));
    const cases = this.cases.map(item => {
      const outcome = item.status === 'passed' ? '' : item.status === 'skipped'
        ? '<skipped/>' : `<failure message="${xml(item.status)}">${xml(item.error)}</failure>`;
      return `<testcase classname="${xml(item.classname)}" name="${xml(item.name)}" time="${item.duration}">${outcome}</testcase>`;
    }).join('\n');
    fs.writeFileSync(path.join(this.directory, 'browser.xml'),
      `<?xml version="1.0" encoding="UTF-8"?><testsuites><testsuite name="Navegador Chromium">${cases}</testsuite></testsuites>`);
  }
}
