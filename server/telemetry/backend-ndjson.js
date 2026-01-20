'use strict'

const fs = require('fs')
const path = require('path')

const LOG_DIR = path.join(__dirname)
const LOG_FILE = path.join(LOG_DIR, 'events.ndjson')

function ensureDir() {
  if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true })
}

function emit(event) {
  try {
    ensureDir()
    fs.appendFileSync(LOG_FILE, JSON.stringify(event) + '\n', 'utf8')
  } catch (e) {
    console.error('ndjson backend write failed', e)
  }
}

module.exports = { emit }
