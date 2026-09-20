"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

export function AuditForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [forceRerun, setForceRerun] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const response = await fetch("/api/audit", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url, forceRerun }),
      });
      const data = (await response.json().catch(() => ({}))) as {
        id?: string;
        error?: string;
      };

      if (!response.ok || !data.id) {
        setError(data.error ?? "The audit failed.");
        setPending(false);
        return;
      }

      router.push(`/report/${data.id}`);
    } catch {
      setError("Could not reach the server.");
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-700">
          Page URL
        </label>
        <input
          id="url"
          name="url"
          type="text"
          inputMode="url"
          placeholder="https://example.com/landing-page"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          required
          disabled={pending}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-gray-500 focus:outline-none disabled:bg-gray-100"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input
          type="checkbox"
          checked={forceRerun}
          onChange={(event) => setForceRerun(event.target.checked)}
          disabled={pending}
          className="h-4 w-4 rounded border-gray-300"
        />
        Force a fresh run, even if this URL was audited in the last 7 days
      </label>

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "Analyzing..." : "Run audit"}
      </button>

      {pending ? (
        <p className="text-sm text-gray-600">
          Fetching the page and scoring it. This usually takes 30 to 60 seconds.
        </p>
      ) : null}
    </form>
  );
}
