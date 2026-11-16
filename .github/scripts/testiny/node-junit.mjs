// JUnit nativo conserva los estados; añadimos el archivo para agrupar por módulo.
import { junit } from 'node:test/reporters';
import path from 'node:path';

export default async function* report(events) {
  async function* withFile() {
    for await (const event of events) {
      const data = event.data;
      if (data?.file && typeof data.name === 'string') {
        const file = path.relative(process.cwd(), data.file).replaceAll('\\', '/');
        const name = data.name === data.file ? '[archivo de pruebas]' : data.name;
        yield { ...event, data: { ...data, name: `${file}::${name}` } };
      } else {
        yield event;
      }
    }
  }
  yield* junit(withFile());
}
