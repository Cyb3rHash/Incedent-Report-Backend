const express = require("express");

// PUBLIC_INTERFACE
function createMetaRouter({ config }) {
  /** Express router for health and API docs endpoints. */
  const router = express.Router();

  router.get("/health", (req, res) => {
    res.json({ ok: true, service: "Incedent-Report-Backend", env: config.nodeEnv });
  });

  router.get("/docs", (req, res) => {
    res.type("text/plain").send(
      [
        "Incident Report Backend API",
        "",
        "Base URL: /api",
        "",
        "Endpoints:",
        "GET    /api/health",
        "GET    /api/incidents?status=&severity=&q=&limit=&offset=&sort=",
        "POST   /api/incidents",
        "GET    /api/incidents/:id",
        "PATCH  /api/incidents/:id",
        "GET    /api/incidents/:id/events",
        "POST   /api/incidents/:id/events",
        "",
        "Schema:",
        "- Apply schema.sql to your Neon database (SQL editor) before using the API.",
      ].join("\n")
    );
  });

  return router;
}

module.exports = { createMetaRouter };
