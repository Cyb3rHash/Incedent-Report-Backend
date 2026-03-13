const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");

const { createIncidentsRouter } = require("./routes/incidentsRoutes");
const { createMetaRouter } = require("./routes/metaRoutes");

/**
 * Builds the Express app.
 * Keeps framework wiring here; domain logic lives in flows.
 */
function createApp({ config, incidentsFlow, logger }) {
  const app = express();

  if (config.trustProxy) app.set("trust proxy", 1);

  app.use(helmet());
  app.use(
    cors({
      origin: config.cors.allowedOrigins,
      methods: config.cors.allowedMethods,
      allowedHeaders: config.cors.allowedHeaders,
      maxAge: config.cors.maxAge,
      credentials: true,
    })
  );

  // Request timeout boundary (best-effort)
  app.use((req, res, next) => {
    res.setTimeout(config.requestTimeoutMs, () => {
      logger.warn("request_timeout", { path: req.path, method: req.method });
      if (!res.headersSent) res.status(504).json({ error: "timeout", message: "Request timed out" });
    });
    next();
  });

  app.use(express.json({ limit: "1mb" }));

  app.use(
    rateLimit({
      windowMs: config.rateLimit.windowSeconds * 1000,
      max: config.rateLimit.max,
      standardHeaders: true,
      legacyHeaders: false,
    })
  );

  // Routes
  app.use("/api", createMetaRouter({ config }));
  app.use("/api/incidents", createIncidentsRouter({ incidentsFlow }));

  // 404
  app.use((req, res) => {
    res.status(404).json({ error: "not_found", message: "Route not found" });
  });

  // Error boundary
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    logger.error("unhandled_error", { message: err?.message, name: err?.name });
    res.status(500).json({ error: "internal_error", message: "Unexpected server error" });
  });

  return app;
}

module.exports = { createApp };
