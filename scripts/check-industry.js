/**
 * 校验脚本:industry.js 引用的 data 路径存在、getElementById 的 id 在 4 个行业页 HTML 中存在。
 * 用法: node scripts/check-industry.js
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const jsPath = path.join(root, 'assets/js/industry.js');
const pages = [
  'industry-chemical.html',
  'industry-electronics.html',
  'industry-automotive.html',
  'industry-eu-export.html'
];

let errors = 0;

// 1) JS 语法已由 node --check 校验;此处检查 DATA 引用的 data 路径
const js = fs.readFileSync(jsPath, 'utf8');
const dataPaths = [...js.matchAll(/'(data\/[^']+\.json)'/g)].map(m => m[1]);
console.log('== JS 引用的数据文件 ==');
for (const p of [...new Set(dataPaths)]) {
  const ok = fs.existsSync(path.join(root, p));
  console.log(`${ok ? 'OK  ' : 'MISS'} ${p}`);
  if (!ok) errors++;
}

// 2) getElementById 的 id 在每个页面 HTML 中存在
const ids = [...new Set([...js.matchAll(/\$\('([^']+)'\)/g)].map(m => m[1]))];
// 动态拼接的 id:fail 占位列表 + 'rec-' + type
const failMatch = js.match(/\[([^\]]*)\]\.forEach\(fail\)/);
if (failMatch) {
  for (const m of failMatch[1].matchAll(/'([^']+)'/g)) ids.push(m[1]);
}
['field', 'template', 'plugin'].forEach(t => ids.push('rec-' + t));
console.log('\n== getElementById 引用的 id ==');
for (const page of pages) {
  const html = fs.readFileSync(path.join(root, page), 'utf8');
  const missing = ids.filter(id => !html.includes(`id="${id}"`));
  console.log(`${page}: ${missing.length ? '缺少 ' + missing.join(', ') : '全部 ' + ids.length + ' 个 id 存在'}`);
  errors += missing.length;
}

// 3) body[data-industry] 与 industry.js 配置一致
console.log('\n== body data-industry ==');
const cfgIndustries = [...js.matchAll(/^    '([^']+)': \{/gm)].map(m => m[1]);
for (const page of pages) {
  const html = fs.readFileSync(path.join(root, page), 'utf8');
  const m = html.match(/<body data-industry="([^"]+)">/);
  const ok = m && cfgIndustries.includes(m[1]);
  console.log(`${ok ? 'OK  ' : 'BAD '} ${page}: data-industry="${m ? m[1] : '(未找到)'}"`);
  if (!ok) errors++;
}

console.log(errors ? `\n失败: ${errors} 个问题` : '\n全部校验通过');
process.exit(errors ? 1 : 0);
