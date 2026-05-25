const { app, BrowserWindow, shell } = require('electron')
const childProcess = require('child_process')
const fs = require('fs')
const http = require('http')
const net = require('net')
const path = require('path')

let mainWindow = null
let statusWindow = null
let mysqlProcess = null
let backendProcess = null
let staticServer = null

const singleInstanceLock = app.requestSingleInstanceLock()
if (!singleInstanceLock) {
  app.quit()
}

const isPackaged = app.isPackaged
const projectRoot = path.resolve(__dirname, '..')

function resourcePath(...parts) {
  return isPackaged ? path.join(process.resourcesPath, ...parts) : path.join(projectRoot, ...parts)
}

function desktopResourcePath(...parts) {
  return isPackaged ? path.join(process.resourcesPath, ...parts) : path.join(__dirname, ...parts)
}

function userDataPath(...parts) {
  return path.join(app.getPath('userData'), ...parts)
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true })
  return dir
}

function setStatus(message) {
  if (!statusWindow || statusWindow.isDestroyed()) return
  statusWindow.webContents.executeJavaScript(
    `document.getElementById('status').textContent = ${JSON.stringify(message)}`,
  ).catch(() => {})
}

function appendLog(fileName, chunk) {
  const logDir = ensureDir(userDataPath('logs'))
  fs.appendFileSync(path.join(logDir, fileName), chunk)
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address()
      server.close(() => resolve(port))
    })
    server.on('error', reject)
  })
}

function waitForTcp(port, timeoutMs = 30000) {
  const start = Date.now()
  return new Promise((resolve, reject) => {
    function tryConnect() {
      const socket = net.createConnection({ host: '127.0.0.1', port })
      socket.once('connect', () => {
        socket.destroy()
        resolve()
      })
      socket.once('error', () => {
        socket.destroy()
        if (Date.now() - start > timeoutMs) {
          reject(new Error(`Timed out waiting for port ${port}`))
          return
        }
        setTimeout(tryConnect, 400)
      })
    }
    tryConnect()
  })
}

function waitForHttp(url, timeoutMs = 30000) {
  const start = Date.now()
  return new Promise((resolve, reject) => {
    function tryRequest() {
      http.get(url, (response) => {
        response.resume()
        if (response.statusCode && response.statusCode < 500) {
          resolve()
          return
        }
        retry()
      }).on('error', retry)
    }
    function retry() {
      if (Date.now() - start > timeoutMs) {
        reject(new Error(`Timed out waiting for ${url}`))
        return
      }
      setTimeout(tryRequest, 500)
    }
    tryRequest()
  })
}

function mysqlPaths() {
  const root = desktopResourcePath('runtime', 'mysql')
  return {
    root,
    mysqld: path.join(root, 'bin', 'mysqld.exe'),
    mysql: path.join(root, 'bin', 'mysql.exe'),
  }
}

function spawnLogged(command, args, options, logName) {
  const child = childProcess.spawn(command, args, {
    windowsHide: true,
    ...options,
  })
  child.stdout.on('data', (chunk) => appendLog(logName, chunk))
  child.stderr.on('data', (chunk) => appendLog(logName, chunk))
  return child
}

async function initializeMysqlData(mysql, dataDir) {
  const marker = path.join(dataDir, 'auto.cnf')
  if (fs.existsSync(marker)) return
  ensureDir(dataDir)
  setStatus('Initializing database files...')
  await new Promise((resolve, reject) => {
    const child = spawnLogged(
      mysql.mysqld,
      [
        '--no-defaults',
        `--basedir=${mysql.root}`,
        `--datadir=${dataDir}`,
        '--initialize-insecure',
        '--console',
      ],
      {},
      'mysql-init.log',
    )
    child.once('exit', (code) => {
      if (code === 0) resolve()
      else reject(new Error(`MySQL initialization failed with exit code ${code}`))
    })
  })
}

async function startMysql(port) {
  const mysql = mysqlPaths()
  if (!fs.existsSync(mysql.mysqld) || !fs.existsSync(mysql.mysql)) {
    throw new Error(`MySQL runtime not found at ${mysql.root}. Put the portable MySQL server there before packaging.`)
  }
  const dataDir = ensureDir(userDataPath('mysql-data'))
  await initializeMysqlData(mysql, dataDir)
  setStatus('Starting database...')
  mysqlProcess = spawnLogged(
    mysql.mysqld,
    [
      '--no-defaults',
      `--basedir=${mysql.root}`,
      `--datadir=${dataDir}`,
      `--port=${port}`,
      '--bind-address=127.0.0.1',
      '--mysqlx=0',
      '--console',
    ],
    {},
    'mysql.log',
  )
  await waitForTcp(port, 45000)
  return mysql
}

async function runMysqlSql(mysql, port, sql) {
  await new Promise((resolve, reject) => {
    const child = spawnLogged(
      mysql.mysql,
      ['--protocol=tcp', '-h127.0.0.1', `-P${port}`, '-uroot'],
      {},
      'mysql-schema.log',
    )
    child.stdin.write(sql)
    child.stdin.end()
    child.once('exit', (code) => {
      if (code === 0) resolve()
      else reject(new Error(`MySQL schema command failed with exit code ${code}`))
    })
  })
}

async function ensureDatabaseInitialized(mysql, port) {
  const marker = userDataPath('schema-initialized.txt')
  if (fs.existsSync(marker)) return
  setStatus('Initializing workspace schema...')
  const schemaPath = resourcePath('db', 'creator_workspace_minimal.sql')
  const schema = fs.readFileSync(schemaPath, 'utf8')
  const sql = [
    'CREATE DATABASE IF NOT EXISTS portfolio_library DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;',
    'USE portfolio_library;',
    schema,
  ].join('\n')
  await runMysqlSql(mysql, port, sql)
  fs.writeFileSync(marker, new Date().toISOString(), 'utf8')
}

async function startBackend(apiPort, mysqlPort) {
  setStatus('Starting API...')
  const env = {
    ...process.env,
    DB_HOST: '127.0.0.1',
    DB_PORT: String(mysqlPort),
    DB_USER: 'root',
    DB_PASSWORD: '',
    DB_NAME: 'portfolio_library',
    FLASK_HOST: '127.0.0.1',
    FLASK_PORT: String(apiPort),
    FLASK_DEBUG: 'false',
    UPLOAD_ROOT: ensureDir(userDataPath('uploads')),
    EXPORT_ROOT: ensureDir(userDataPath('exports')),
  }
  const backendExe = isPackaged
    ? resourcePath('backend', 'portfolio-backend.exe')
    : resourcePath('backend', 'dist', 'portfolio-backend.exe')
  if (fs.existsSync(backendExe)) {
    backendProcess = spawnLogged(backendExe, [], { env }, 'backend.log')
  } else {
    backendProcess = spawnLogged('python', [resourcePath('backend', 'app.py')], { env, cwd: resourcePath('backend') }, 'backend.log')
  }
  await waitForHttp(`http://127.0.0.1:${apiPort}/api`, 30000)
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase()
  return {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
  }[ext] || 'application/octet-stream'
}

async function startStaticServer() {
  const distDir = isPackaged ? resourcePath('frontend') : resourcePath('frontend', 'dist')
  if (!fs.existsSync(path.join(distDir, 'index.html'))) {
    throw new Error(`Frontend build not found at ${distDir}. Run npm --prefix frontend run build first.`)
  }
  const port = await getFreePort()
  staticServer = http.createServer((request, response) => {
    const urlPath = decodeURIComponent((request.url || '/').split('?')[0])
    const normalized = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, '')
    let filePath = path.join(distDir, normalized)
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      filePath = path.join(distDir, 'index.html')
    }
    if (!filePath.startsWith(distDir)) {
      response.writeHead(403)
      response.end('Forbidden')
      return
    }
    response.writeHead(200, { 'Content-Type': contentType(filePath) })
    fs.createReadStream(filePath).pipe(response)
  })
  await new Promise((resolve) => staticServer.listen(port, '127.0.0.1', resolve))
  return port
}

async function createMainWindow(apiPort, uiPort) {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 980,
    minHeight: 700,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      additionalArguments: [`--api-base=http://127.0.0.1:${apiPort}/api`],
    },
  })
  mainWindow.once('ready-to-show', () => {
    if (statusWindow && !statusWindow.isDestroyed()) statusWindow.close()
    mainWindow.show()
  })
  await mainWindow.loadURL(`http://127.0.0.1:${uiPort}`)
}

async function createStatusWindow() {
  statusWindow = new BrowserWindow({
    width: 620,
    height: 420,
    resizable: false,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  statusWindow.once('ready-to-show', () => statusWindow.show())
  await statusWindow.loadFile(path.join(__dirname, 'loading.html'))
}

async function boot() {
  await createStatusWindow()
  ensureDir(userDataPath('logs'))
  ensureDir(userDataPath('uploads'))
  ensureDir(userDataPath('exports'))
  const mysqlPort = await getFreePort()
  const apiPort = await getFreePort()
  const mysql = await startMysql(mysqlPort)
  await ensureDatabaseInitialized(mysql, mysqlPort)
  await startBackend(apiPort, mysqlPort)
  setStatus('Opening Portfolio Library...')
  const uiPort = await startStaticServer()
  await createMainWindow(apiPort, uiPort)
}

function showBootError(error) {
  const message = `${error.message}\n\nLogs: ${userDataPath('logs')}`
  if (statusWindow && !statusWindow.isDestroyed()) {
    statusWindow.webContents.executeJavaScript(`
      document.querySelector('p').textContent = ${JSON.stringify(message)};
      document.getElementById('status').textContent = 'Startup failed. See logs.';
    `).catch(() => {})
  }
}

async function shutdownServices() {
  if (backendProcess && !backendProcess.killed) backendProcess.kill()
  if (mysqlProcess && !mysqlProcess.killed) mysqlProcess.kill()
  if (staticServer) {
    await new Promise((resolve) => staticServer.close(resolve))
  }
}

app.whenReady().then(() => {
  if (!singleInstanceLock) return
  boot().catch((error) => {
    appendLog('desktop.log', `${error.stack || error.message}\n`)
    showBootError(error)
  })
})

app.on('second-instance', () => {
  const target = mainWindow || statusWindow
  if (!target || target.isDestroyed()) return
  if (target.isMinimized()) target.restore()
  target.focus()
})

app.on('window-all-closed', () => {
  shutdownServices().finally(() => app.quit())
})

app.on('before-quit', () => {
  if (backendProcess && !backendProcess.killed) backendProcess.kill()
  if (mysqlProcess && !mysqlProcess.killed) mysqlProcess.kill()
})

app.on('web-contents-created', (_event, contents) => {
  contents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
})
