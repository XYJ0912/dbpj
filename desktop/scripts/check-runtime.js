const fs = require('fs')
const path = require('path')

const mysqlRoot = path.resolve(__dirname, '..', 'runtime', 'mysql')
const required = [
  path.join(mysqlRoot, 'bin', 'mysqld.exe'),
  path.join(mysqlRoot, 'bin', 'mysql.exe'),
]

const missing = required.filter((item) => !fs.existsSync(item))
if (missing.length) {
  console.error('MySQL portable runtime is missing.')
  console.error(`Expected root: ${mysqlRoot}`)
  console.error('Download MySQL Community Server for Windows x64 as a ZIP archive, then copy its contents into desktop/runtime/mysql.')
  console.error('Missing files:')
  for (const item of missing) console.error(`- ${item}`)
  process.exit(1)
}

console.log('MySQL runtime check passed.')
