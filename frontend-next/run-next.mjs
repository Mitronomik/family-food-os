// Set the opt-out before the Next CLI and its child processes initialize.
process.env.NEXT_TELEMETRY_DISABLED = "1";
// Next prints telemetry in debug mode before checking the opt-out.
delete process.env.NEXT_TELEMETRY_DEBUG;
await import("next/dist/bin/next");
