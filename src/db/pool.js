const { Pool } = require("pg");

/**
 * Creates a pg Pool configured for Neon/Postgres.
 */
function createPool(databaseUrl) {
  return new Pool({
    connectionString: databaseUrl,
    // Neon uses SSL; DATABASE_URL already includes sslmode=require.
    // pg will infer ssl params from connection string; we keep config minimal here.
  });
}

/**
 * Canonical query helper to add context and keep callsites uniform.
 */
async function query(pool, operation, text, params) {
  try {
    const res = await pool.query(text, params);
    return res;
  } catch (e) {
    const err = new Error(`DB query failed (${operation}): ${e.message}`);
    err.name = "DbQueryError";
    err.cause = e;
    throw err;
  }
}

module.exports = { createPool, query };
