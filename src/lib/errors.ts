/**
 * Error type for anything that should be reported back to the owner as a
 * readable message instead of a stack trace. Every throw site sets a status
 * code so the API route can pass it straight through.
 */
export class AuditError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, options?: { status?: number; code?: string }) {
    super(message);
    this.name = "AuditError";
    this.status = options?.status ?? 400;
    this.code = options?.code ?? "audit_error";
  }
}

export function toErrorResponse(error: unknown): { message: string; status: number; code: string } {
  if (error instanceof AuditError) {
    return { message: error.message, status: error.status, code: error.code };
  }
  if (error instanceof Error) {
    return { message: error.message, status: 500, code: "unexpected_error" };
  }
  return { message: "Something went wrong.", status: 500, code: "unexpected_error" };
}
