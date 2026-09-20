import Link from "next/link";
import { AuditForm } from "@/components/audit-form";
import { LoginForm } from "@/components/login-form";
import { LogoutButton } from "@/components/logout-button";
import { hasValidSession } from "@/lib/auth";
import { REUSE_WINDOW_DAYS } from "@/lib/config";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const signedIn = await hasValidSession();

  if (!signedIn) {
    return <LoginForm heading="CRO Page Audit" />;
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Run a page audit</h1>
          <p className="mt-2 text-sm text-gray-600">
            Paste a page URL. The report is saved behind a private link you can send to the prospect.
          </p>
        </div>
        <LogoutButton />
      </div>

      <div className="mt-8 rounded-lg border border-gray-200 bg-white p-6">
        <AuditForm />
      </div>

      <p className="mt-6 text-sm text-gray-600">
        A URL audited in the last {REUSE_WINDOW_DAYS} days returns its existing report unless you force a
        fresh run.
      </p>

      <p className="mt-8 text-sm">
        <Link href="/dashboard" className="text-gray-900 underline underline-offset-2">
          See past audits
        </Link>
      </p>
    </main>
  );
}
