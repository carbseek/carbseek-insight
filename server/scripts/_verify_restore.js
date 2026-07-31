// Verify recommendation id=1 desc matches the original from git HEAD.
const { execSync } = require('node:child_process');
const db = require('C:/Users/lipen/Documents/kimi/Workspaces/carbseek/insight-update/server/db/connection');

const headJson = execSync('git show HEAD:data/industries/recommendations.json', {
  cwd: 'C:/Users/lipen/Documents/kimi/Workspaces/carbseek/insight-update',
  encoding: 'utf-8',
});
const orig = JSON.parse(headJson)['化工'][0];
const row = db.prepare('SELECT * FROM recommendations WHERE id = 1').get();

console.log('HEAD 原始 desc:', JSON.stringify(orig.desc));
console.log('DB 当前 desc :', JSON.stringify(row.description));
console.log('一致:', row.description === orig.desc);
if (row.description !== orig.desc) {
  db.prepare('UPDATE recommendations SET description = ? WHERE id = 1').run(orig.desc);
  const fixed = db.prepare('SELECT description FROM recommendations WHERE id = 1').get();
  console.log('已从 HEAD 还原,现在:', JSON.stringify(fixed.description));
  console.log('还原后一致:', fixed.description === orig.desc);
}
