const { query } = require("../db/pool");
const {
  CreateIncidentInput,
  UpdateIncidentInput,
  ListIncidentsQuery,
} = require("../domain/incidentSchemas");

/**
 * Flow name: IncidentsFlow
 * Single entrypoints for incident use-cases to avoid patchy logic in routes.
 *
 * Contract:
 * - Inputs are plain JS objects, validated with Zod at flow boundary.
 * - Outputs are row objects returned from Postgres.
 * - Errors:
 *   - ValidationError (name) for invalid inputs
 *   - DbQueryError for database failures
 * Side effects:
 * - Executes SQL against Postgres.
 */
class IncidentsFlow {
  constructor({ pool, logger }) {
    this.pool = pool;
    this.logger = logger;
  }

  _validationError(zodError) {
    const err = new Error(zodError.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; "));
    err.name = "ValidationError";
    err.cause = zodError;
    return err;
  }

  async createIncident(input) {
    const parsed = CreateIncidentInput.safeParse(input);
    if (!parsed.success) throw this._validationError(parsed.error);

    const op = "incidents.createIncident";
    this.logger.info("flow_start", { op });

    const d = parsed.data;
    const res = await query(
      this.pool,
      op,
      `
        INSERT INTO incidents (title, description, severity, reported_by, assigned_to, occurred_at)
        VALUES ($1, $2, COALESCE($3, 'medium'), $4, $5, $6)
        RETURNING *
      `,
      [
        d.title,
        d.description,
        d.severity ?? null,
        d.reported_by ?? null,
        d.assigned_to ?? null,
        d.occurred_at ?? null,
      ]
    );

    this.logger.info("flow_end", { op, incident_id: res.rows[0].id });
    return res.rows[0];
  }

  async getIncidentById(id) {
    const op = "incidents.getIncidentById";
    this.logger.info("flow_start", { op, incident_id: id });

    const res = await query(this.pool, op, `SELECT * FROM incidents WHERE id = $1`, [id]);
    const row = res.rows[0] || null;

    this.logger.info("flow_end", { op, found: !!row, incident_id: id });
    return row;
  }

  async listIncidents(queryObj) {
    const parsed = ListIncidentsQuery.safeParse(queryObj);
    if (!parsed.success) throw this._validationError(parsed.error);

    const op = "incidents.listIncidents";
    const q = parsed.data;
    this.logger.info("flow_start", { op, filters: { status: q.status, severity: q.severity, q: q.q } });

    const where = [];
    const params = [];
    let p = 1;

    if (q.status) {
      where.push(`status = $${p++}`);
      params.push(q.status);
    }
    if (q.severity) {
      where.push(`severity = $${p++}`);
      params.push(q.severity);
    }
    if (q.q) {
      where.push(`(title ILIKE $${p} OR description ILIKE $${p})`);
      params.push(`%${q.q}%`);
      p++;
    }

    const orderBy =
      q.sort === "created_at_asc"
        ? "created_at ASC"
        : q.sort === "updated_at_desc"
          ? "updated_at DESC"
          : q.sort === "updated_at_asc"
            ? "updated_at ASC"
            : "created_at DESC";

    // limit/offset always present due to defaults
    const limitParam = `$${p++}`;
    params.push(q.limit);
    const offsetParam = `$${p++}`;
    params.push(q.offset);

    const sql = `
      SELECT *
      FROM incidents
      ${where.length ? `WHERE ${where.join(" AND ")}` : ""}
      ORDER BY ${orderBy}
      LIMIT ${limitParam}
      OFFSET ${offsetParam}
    `;

    const res = await query(this.pool, op, sql, params);

    this.logger.info("flow_end", { op, count: res.rows.length });
    return res.rows;
  }

  async updateIncident(id, patch) {
    const parsed = UpdateIncidentInput.safeParse(patch);
    if (!parsed.success) throw this._validationError(parsed.error);

    const op = "incidents.updateIncident";
    this.logger.info("flow_start", { op, incident_id: id });

    const fields = [];
    const params = [];
    let p = 1;

    const d = parsed.data;
    for (const [key, value] of Object.entries(d)) {
      fields.push(`${key} = $${p++}`);
      params.push(value === undefined ? null : value);
    }

    params.push(id);
    const sql = `
      UPDATE incidents
      SET ${fields.join(", ")}
      WHERE id = $${p}
      RETURNING *
    `;

    const res = await query(this.pool, op, sql, params);
    const row = res.rows[0] || null;

    this.logger.info("flow_end", { op, updated: !!row, incident_id: id });
    return row;
  }

  async addEvent(incidentId, input) {
    const op = "incidents.addEvent";
    const schema = require("zod").z.object({
      event_type: require("zod").z.string().min(1).max(100),
      message: require("zod").z.string().min(1).max(2000),
    });

    const parsed = schema.safeParse(input);
    if (!parsed.success) throw this._validationError(parsed.error);

    this.logger.info("flow_start", { op, incident_id: incidentId });

    const res = await query(
      this.pool,
      op,
      `
        INSERT INTO incident_events (incident_id, event_type, message)
        VALUES ($1, $2, $3)
        RETURNING *
      `,
      [incidentId, parsed.data.event_type, parsed.data.message]
    );

    this.logger.info("flow_end", { op, incident_id: incidentId, event_id: res.rows[0].id });
    return res.rows[0];
  }

  async listEvents(incidentId) {
    const op = "incidents.listEvents";
    this.logger.info("flow_start", { op, incident_id: incidentId });

    const res = await query(
      this.pool,
      op,
      `SELECT * FROM incident_events WHERE incident_id = $1 ORDER BY created_at DESC`,
      [incidentId]
    );

    this.logger.info("flow_end", { op, incident_id: incidentId, count: res.rows.length });
    return res.rows;
  }
}

module.exports = { IncidentsFlow };
