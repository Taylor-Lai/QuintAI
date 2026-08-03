import { spawn } from 'node:child_process'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { build, preview } from 'vite'

const host = '127.0.0.1'
const port = 4173
const playwrightCli = fileURLToPath(
  new URL('../node_modules/@playwright/test/cli.js', import.meta.url),
)

await build({
  logLevel: 'warn',
})

const server = await preview({
  preview: { host, port },
  logLevel: 'warn',
})

let exitCode

try {
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
  await new Promise((resolve, reject) => {
    server.httpServer.close((error) => {
      if (error) reject(error)
      else resolve()
    })
  })
}

process.exitCode = exitCode
