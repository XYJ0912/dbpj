const { contextBridge } = require('electron')

function argumentValue(prefix) {
  const item = process.argv.find((value) => value.startsWith(prefix))
  return item ? item.slice(prefix.length) : ''
}

contextBridge.exposeInMainWorld('__APP_CONFIG__', {
  apiBase: argumentValue('--api-base='),
})
