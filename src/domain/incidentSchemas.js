const { z } = require("zod");

const IncidentStatus = z.enum(["open", "acknowledged", "in_progress", "resolved", "closed"]);
const IncidentSeverity = z.enum(["low", "medium", "high", "critical"]);

const CreateIncidentInput = z.object({
  title: z.string().min(1).max(200),
  description: z.string().min(1).max(10000),
  severity: IncidentSeverity.optional(),
  reported_by: z.string().min(1).max(200).optional(),
  assigned_to: z.string().min(1).max(200).optional(),
  occurred_at: z.string().datetime().optional(), // ISO string
});

const UpdateIncidentInput = z
  .object({
    title: z.string().min(1).max(200).optional(),
    description: z.string().min(1).max(10000).optional(),
    status: IncidentStatus.optional(),
    severity: IncidentSeverity.optional(),
    reported_by: z.string().min(1).max(200).optional().nullable(),
    assigned_to: z.string().min(1).max(200).optional().nullable(),
    occurred_at: z.string().datetime().optional().nullable(),
  })
  .refine((obj) => Object.keys(obj).length > 0, { message: "At least one field must be provided" });

const ListIncidentsQuery = z.object({
  status: IncidentStatus.optional(),
  severity: IncidentSeverity.optional(),
  q: z.string().min(1).max(200).optional(),
  limit: z.coerce.number().int().positive().max(200).default(50),
  offset: z.coerce.number().int().nonnegative().default(0),
  sort: z.enum(["created_at_desc", "created_at_asc", "updated_at_desc", "updated_at_asc"]).default("created_at_desc"),
});

module.exports = {
  IncidentStatus,
  IncidentSeverity,
  CreateIncidentInput,
  UpdateIncidentInput,
  ListIncidentsQuery,
};
