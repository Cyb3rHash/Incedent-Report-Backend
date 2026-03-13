const express = require("express");

/**
 * Maps domain/flow errors to HTTP responses at the boundary only.
 */
function sendError(res, err) {
  if (err && err.name === "ValidationError") {
    return res.status(400).json({ error: "validation_error", message: err.message });
  }
  if (err && err.name === "DbQueryError") {
    return res.status(500).json({ error: "db_error", message: "Database operation failed" });
  }
  return res.status(500).json({ error: "internal_error", message: "Unexpected server error" });
}

// PUBLIC_INTERFACE
function createIncidentsRouter({ incidentsFlow }) {
  /** Express router for incident CRUD endpoints. */
  const router = express.Router();

  router.get("/", async (req, res) => {
    try {
      const incidents = await incidentsFlow.listIncidents(req.query);
      res.json({ data: incidents });
    } catch (e) {
      sendError(res, e);
    }
  });

  router.post("/", async (req, res) => {
    try {
      const incident = await incidentsFlow.createIncident(req.body);
      res.status(201).json({ data: incident });
    } catch (e) {
      sendError(res, e);
    }
  });

  router.get("/:id", async (req, res) => {
    try {
      const incident = await incidentsFlow.getIncidentById(req.params.id);
      if (!incident) return res.status(404).json({ error: "not_found", message: "Incident not found" });
      res.json({ data: incident });
    } catch (e) {
      sendError(res, e);
    }
  });

  router.patch("/:id", async (req, res) => {
    try {
      const incident = await incidentsFlow.updateIncident(req.params.id, req.body);
      if (!incident) return res.status(404).json({ error: "not_found", message: "Incident not found" });
      res.json({ data: incident });
    } catch (e) {
      sendError(res, e);
    }
  });

  router.get("/:id/events", async (req, res) => {
    try {
      const events = await incidentsFlow.listEvents(req.params.id);
      res.json({ data: events });
    } catch (e) {
      sendError(res, e);
    }
  });

  router.post("/:id/events", async (req, res) => {
    try {
      const event = await incidentsFlow.addEvent(req.params.id, req.body);
      res.status(201).json({ data: event });
    } catch (e) {
      sendError(res, e);
    }
  });

  return router;
}

module.exports = { createIncidentsRouter };
