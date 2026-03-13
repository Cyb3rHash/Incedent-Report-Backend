/**
 * Minimal structured logger.
 * Logs JSON lines for easy searching and ingestion.
 */
class Logger {
  info(message, fields = {}) {
    console.log(JSON.stringify({ level: "info", message, ...fields, ts: new Date().toISOString() }));
  }

  warn(message, fields = {}) {
    console.warn(JSON.stringify({ level: "warn", message, ...fields, ts: new Date().toISOString() }));
  }

  error(message, fields = {}) {
    console.error(JSON.stringify({ level: "error", message, ...fields, ts: new Date().toISOString() }));
  }
}

module.exports = { Logger };
