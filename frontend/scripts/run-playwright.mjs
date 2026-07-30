import { spawn } from 'node:child_process'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

const host = '127.0.0.1'
const port = 4173
const playwrightCli = fileURLToPath(
  new URL('../node_modules/@playwright/test/cli.js', import.meta.url),
)

const server = await createServer({
  server: { host, port },
  logLevel: 'warn',
})

let exitCode

try {
  await server.listen()
  exitCode = await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [playwrightCli, 'test'], {
      cwd: process.cwd(),
      env: process.env,
      stdio: 'inherit',
    })
    child.once('error', reject)
    child.once('exit', (code) => resolve(code ?? 1))
  })
} finally {
  await server.close()
}

process.exitCode = exitCode
