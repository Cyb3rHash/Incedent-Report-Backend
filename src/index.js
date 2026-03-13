require("dotenv").config();

const { loadConfigFromEnv } = require("./config");
const { Logger } = require("./lib/logger");
const { createPool } = require("./db/pool");
const { IncidentsFlow } = require("./flows/incidentsFlow");
const { createApp } = require("./app");

/**
 * Entry point for the backend service.
 * - Loads config
 * - Creates DB pool
 * - Wires flows & routes
 * - Starts HTTP server
 */
async function main() {
  const logger = new Logger();
  const config = loadConfigFromEnv(process.env);

  const pool = createPool(config.databaseUrl);
  const incidentsFlow = new IncidentsFlow({ pool, logger });

  const app = createApp({ config, incidentsFlow, logger });

  const server = app.listen(config.port, config.host, () => {
    logger.info("server_started", { host: config.host, port: config.port, env: config.nodeEnv });
  });

  // Graceful shutdown
  const shutdown = async (signal) => {
    logger.warn("shutdown_signal", { signal });
    server.close(async () => {
      try {
        await pool.end();
        logger.info("shutdown_complete");
        process.exit(0);
      } catch (e) {
        logger.error("shutdown_error", { message: e?.message });
        process.exit(1);
      }
    });
  };

  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e);
  process.exit(1);
});
