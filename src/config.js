const { z } = require("zod");

/**
 * Loads and validates environment configuration.
 * Keeps env access at the application boundary only.
 */
function loadConfigFromEnv(env) {
  const schema = z.object({
    NODE_ENV: z.string().default("development"),
    HOST: z.string().default("0.0.0.0"),
    PORT: z.coerce.number().int().positive().default(3002),

    DATABASE_URL: z.string().min(1, "DATABASE_URL is required"),

    ALLOWED_ORIGINS: z.string().default("http://localhost:3000"),
    ALLOWED_HEADERS: z.string().default("Content-Type,Authorization,X-Requested-With"),
    ALLOWED_METHODS: z.string().default("GET,POST,PUT,DELETE,PATCH,OPTIONS"),
    CORS_MAX_AGE: z.coerce.number().int().nonnegative().default(3600),

    REQUEST_TIMEOUT_MS: z.coerce.number().int().positive().default(30000),
    RATE_LIMIT_WINDOW_S: z.coerce.number().int().positive().default(60),
    RATE_LIMIT_MAX: z.coerce.number().int().positive().default(100),

    TRUST_PROXY: z
      .string()
      .optional()
      .transform((v) => (v ? v.toLowerCase() === "true" : false)),
  });

  const parsed = schema.safeParse(env);
  if (!parsed.success) {
    const msg = parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; ");
    const err = new Error(`Invalid environment configuration: ${msg}`);
    err.name = "ConfigError";
    throw err;
  }

  const cfg = parsed.data;

  return {
    nodeEnv: cfg.NODE_ENV,
    host: cfg.HOST,
    port: cfg.PORT,
    databaseUrl: cfg.DATABASE_URL,
    cors: {
      allowedOrigins: cfg.ALLOWED_ORIGINS.split(",").map((s) => s.trim()).filter(Boolean),
      allowedHeaders: cfg.ALLOWED_HEADERS.split(",").map((s) => s.trim()).filter(Boolean),
      allowedMethods: cfg.ALLOWED_METHODS.split(",").map((s) => s.trim()).filter(Boolean),
      maxAge: cfg.CORS_MAX_AGE,
    },
    requestTimeoutMs: cfg.REQUEST_TIMEOUT_MS,
    rateLimit: {
      windowSeconds: cfg.RATE_LIMIT_WINDOW_S,
      max: cfg.RATE_LIMIT_MAX,
    },
    trustProxy: cfg.TRUST_PROXY,
  };
}

module.exports = { loadConfigFromEnv };
