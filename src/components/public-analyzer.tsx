"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { PublicSummary } from "@/lib/public-analyzer";

type Step = "url" | "goal" | "traffic" | "analyzing" | "result" | "error";

const TRAFFIC_OPTIONS = ["Search engines", "Paid ads", "Social media", "Email", "Referral or direct"];

/** Shown one after another while the request runs. The last one waits for the response. */
const PROGRESS_STEPS: { title: string; detail: string; ms: number | null }[] = [
  { title: "Loading the page", detail: "Fetching the HTML", ms: 5000 },
  { title: "Reading the content", detail: "Headlines, copy and buttons", ms: 9000 },
  { title: "Looking for friction", detail: "Forms, links and distractions", ms: 9000 },
  { title: "Checking trust signals", detail: "Proof, guarantees and contact details", ms: 9000 },
  { title: "Scoring each factor", detail: "Comparing against the rubric", ms: 12000 },
  { title: "Writing the summary", detail: "Almost there", ms: null },
];

function scoreTone(score: number): { label: string; text: string; bar: string } {
  if (score >= 8) return { label: "Above average", text: "text-green-700", bar: "bg-green-600" };
  if (score >= 6) return { label: "Needs improvement", text: "text-yellow-700", bar: "bg-yellow-500" };
  if (score >= 4) return { label: "Underperforming", text: "text-orange-700", bar: "bg-orange-500" };
  return { label: "Critical", text: "text-red-700", bar: "bg-red-600" };
}

function normalizeInput(raw: string): string | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const withScheme = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  try {
    const parsed = new URL(withScheme);
    return parsed.hostname.includes(".") ? withScheme : null;
  } catch {
    return null;
  }
}

function formatElapsed(seconds: number): string {
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

export function PublicAnalyzer({ bookingUrl }: { bookingUrl: string | null }) {
  const [step, setStep] = useState<Step>("url");
  const [url, setUrl] = useState("");
  const [urlError, setUrlError] = useState(false);
  const [goal, setGoal] = useState("");
  const [traffic, setTraffic] = useState("");

  const [progressIndex, setProgressIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  const [result, setResult] = useState<PublicSummary | null>(null);
  const [error, setError] = useState<{ message: string; limitReached: boolean } | null>(null);

  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [leadPending, setLeadPending] = useState<"email" | "meeting" | null>(null);
  const [leadDone, setLeadDone] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (step === "url" || step === "goal") inputRef.current?.focus();
  }, [step]);

  // Progress steps and elapsed timer while analyzing.
  useEffect(() => {
    if (step !== "analyzing") return;
    const started = Date.now();
    const tick = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 250);

    let timeout: ReturnType<typeof setTimeout>;
    const advance = (index: number) => {
      const ms = PROGRESS_STEPS[index]?.ms;
      if (ms == null) return;
      timeout = setTimeout(() => {
        setProgressIndex(index + 1);
        advance(index + 1);
      }, ms);
    };
    advance(0);

    return () => {
      clearInterval(tick);
      clearTimeout(timeout);
    };
  }, [step]);

  function submitUrl() {
    const normalized = normalizeInput(url);
    if (!normalized) {
      setUrlError(true);
      return;
    }
    setUrlError(false);
    setUrl(normalized);
    setStep("goal");
  }

  async function runAnalysis() {
    setProgressIndex(0);
    setElapsed(0);
    setResult(null);
    setError(null);
    setStep("analyzing");

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url, goal: goal.trim() || undefined, trafficSource: traffic || undefined }),
      });
      const data = (await response.json().catch(() => ({}))) as Partial<PublicSummary> & {
        error?: string;
        limitReached?: boolean;
      };

      if (!response.ok || !data.runId) {
        setError({
          message: data.error ?? "We couldn't analyze that page. It may be blocking automated visits.",
          limitReached: data.limitReached === true,
        });
        setStep("error");
        return;
      }

      setResult(data as PublicSummary);
      setStep("result");
    } catch {
      setError({ message: "Could not reach the server.", limitReached: false });
      setStep("error");
    }
  }

  async function captureLead(wantsMeeting: boolean) {
    if (!result) return;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim())) {
      setEmailError("Please enter a valid email address.");
      return;
    }
    setEmailError(null);
    setLeadPending(wantsMeeting ? "meeting" : "email");

    // Open the booking tab inside the click handler so pop-up blockers allow it.
    const bookingTab = wantsMeeting && bookingUrl ? window.open(bookingUrl, "_blank", "noopener") : null;

    try {
      const response = await fetch(`/api/runs/${result.runId}/lead`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: email.trim(), wantsMeeting }),
      });
      const data = (await response.json().catch(() => ({}))) as { error?: string };
      if (!response.ok) {
        setEmailError(data.error ?? "Something went wrong. Please try again.");
        setLeadPending(null);
        bookingTab?.close();
        return;
      }
      setLeadDone(
        wantsMeeting
          ? "Thanks. Pick a time in the new tab and we'll send the full report before the call."
          : "Thanks. We'll send your full report shortly.",
      );
    } catch {
      setEmailError("Something went wrong. Please try again.");
      setLeadPending(null);
    }
  }

  function reset() {
    setStep("url");
    setGoal("");
    setTraffic("");
    setResult(null);
    setError(null);
    setLeadDone(null);
    setLeadPending(null);
    setEmail("");
  }

  const wizardIndex = step === "url" ? 0 : step === "goal" ? 1 : step === "traffic" ? 2 : 3;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      {wizardIndex < 3 ? (
        <div className="mb-6 flex gap-2" aria-label={`Step ${wizardIndex + 1} of 3`}>
          {[0, 1, 2].map((index) => (
            <span
              key={index}
              className={`h-1.5 flex-1 rounded-full ${index <= wizardIndex ? "bg-gray-900" : "bg-gray-200"}`}
            />
          ))}
        </div>
      ) : null}

      {step === "url" ? (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Which page should we look at?</h3>
          <p className="text-sm text-gray-600">Paste the address of the page you want more conversions from.</p>
          <input
            ref={inputRef}
            type="text"
            inputMode="url"
            placeholder="https://yourwebsite.com/page"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
              if (event.key === "Enter") {
                event.preventDefault();
                submitUrl();
              }
            }}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-gray-500 focus:outline-none"
          />
          {urlError ? <p className="text-sm text-red-700">Please enter a valid URL.</p> : null}
          <button
            type="button"
            onClick={submitUrl}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
          >
            Continue
          </button>
        </div>
      ) : null}

      {step === "goal" ? (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">What is the one thing a visitor should do here?</h3>
          <p className="text-sm text-gray-600">This tells the analysis what success looks like for this page.</p>
          <input
            ref={inputRef}
            type="text"
            placeholder="e.g. Request a quote, start a trial, call us"
            value={goal}
            maxLength={200}
            onChange={(event) => setGoal(event.target.value)}
            onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
              if (event.key === "Enter") {
                event.preventDefault();
                setStep("traffic");
              }
            }}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-gray-500 focus:outline-none"
          />
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setStep("traffic")}
              className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
            >
              Continue
            </button>
            <button
              type="button"
              onClick={() => {
                setGoal("");
                setStep("traffic");
              }}
              className="text-sm text-gray-600 underline underline-offset-2"
            >
              Skip
            </button>
          </div>
        </div>
      ) : null}

      {step === "traffic" ? (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Where do most visitors come from?</h3>
          <p className="text-sm text-gray-600">Someone from an ad expects something different than someone from search.</p>
          <div className="flex flex-wrap gap-2">
            {TRAFFIC_OPTIONS.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setTraffic(option)}
                aria-pressed={traffic === option}
                className={`rounded-full border px-3 py-1.5 text-sm ${
                  traffic === option ? "border-gray-900 bg-gray-900 text-white" : "border-gray-300 text-gray-700"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={runAnalysis}
              className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
            >
              Run the analysis
            </button>
            <button
              type="button"
              onClick={() => {
                setTraffic("");
                runAnalysis();
              }}
              className="text-sm text-gray-600 underline underline-offset-2"
            >
              Skip and run
            </button>
          </div>
        </div>
      ) : null}

      {step === "analyzing" ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Analyzing your page</h3>
            <span className="font-mono text-sm text-gray-500">{formatElapsed(elapsed)}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full bg-gray-900 transition-all duration-500"
              style={{ width: `${Math.min(90, Math.round(((progressIndex + 1) / PROGRESS_STEPS.length) * 100))}%` }}
            />
          </div>
          <ol className="space-y-2">
            {PROGRESS_STEPS.map((item, index) => {
              const state = index < progressIndex ? "done" : index === progressIndex ? "active" : "pending";
              return (
                <li key={item.title} className="flex items-start gap-3 text-sm">
                  <span
                    className={`flex h-6 w-6 flex-none items-center justify-center rounded-full text-xs ${
                      state === "done"
                        ? "bg-green-600 text-white"
                        : state === "active"
                          ? "bg-gray-900 text-white"
                          : "bg-gray-200 text-gray-600"
                    }`}
                  >
                    {state === "done" ? "✓" : state === "active" ? (
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    ) : (
                      index + 1
                    )}
                  </span>
                  <div>
                    <div className={state === "pending" ? "text-gray-500" : "font-medium text-gray-900"}>
                      {item.title}
                    </div>
                    {state === "active" ? <div className="text-gray-600">{item.detail}</div> : null}
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      ) : null}

      {step === "error" && error ? (
        <div className="space-y-4">
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error.limitReached ? error.message : `We couldn't analyze that page. ${error.message}`}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            {bookingUrl ? (
              <a
                href={bookingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
              >
                Book a free review
              </a>
            ) : null}
            {!error.limitReached ? (
              <button type="button" onClick={reset} className="text-sm text-gray-600 underline underline-offset-2">
                Try another URL
              </button>
            ) : null}
          </div>
        </div>
      ) : null}

      {step === "result" && result ? <ResultView result={result} /> : null}

      {step === "result" && result ? (
        <div className="mt-8 space-y-6">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
            <h4 className="font-semibold">Your fixes are ready</h4>
            <p className="mt-1 text-sm text-gray-600">
              We have a prioritized list of what to change on this page. Book a short call and we'll walk you through it.
            </p>
            {bookingUrl ? (
              <a
                href={bookingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
              >
                Get my recommendations
              </a>
            ) : null}
          </div>

          <div className="rounded-lg border border-gray-200 p-5">
            <h4 className="font-semibold">Want the full report by email?</h4>
            {leadDone ? (
              <p className="mt-2 text-sm text-green-700">{leadDone}</p>
            ) : (
              <>
                <p className="mt-1 text-sm text-gray-600">We only use your email to follow up about this report.</p>
                <input
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  disabled={leadPending !== null}
                  className="mt-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-gray-500 focus:outline-none disabled:bg-gray-100"
                />
                {emailError ? <p className="mt-2 text-sm text-red-700">{emailError}</p> : null}
                <div className="mt-3 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => captureLead(false)}
                    disabled={leadPending !== null}
                    className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-900 disabled:opacity-50"
                  >
                    {leadPending === "email" ? "Sending..." : "Just email me the report"}
                  </button>
                  <button
                    type="button"
                    onClick={() => captureLead(true)}
                    disabled={leadPending !== null}
                    className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                  >
                    {leadPending === "meeting" ? "Sending..." : "Email it and book a review"}
                  </button>
                </div>
              </>
            )}
          </div>

          <button type="button" onClick={reset} className="text-sm text-gray-600 underline underline-offset-2">
            Analyze another page
          </button>
        </div>
      ) : null}
    </div>
  );
}

function ResultView({ result }: { result: PublicSummary }) {
  const tone = scoreTone(result.overallScore);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-6">
        <div className="text-center">
          <div className={`text-5xl font-bold ${tone.text}`}>{result.overallScore.toFixed(1)}</div>
          <div className="text-xs text-gray-500">/ 10 score</div>
        </div>
        <div className="min-w-0">
          <div className={`font-semibold ${tone.text}`}>{tone.label}</div>
          <p className="mt-1 break-words text-sm text-gray-600">{result.url}</p>
        </div>
      </div>

      <p className="text-sm text-gray-800">{result.verdict}</p>

      {result.sinsFound.length > 0 ? (
        <div>
          <h4 className="text-sm font-semibold text-gray-900">Conversion killers found</h4>
          <div className="mt-2 flex flex-wrap gap-2">
            {result.sinsFound.map((sin) => (
              <span key={sin} className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
                {sin}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div>
        <h4 className="text-sm font-semibold text-gray-900">Factor by factor</h4>
        <div className="mt-3 space-y-4">
          {result.dimensions.map((dimension) => {
            const dimensionTone = scoreTone(dimension.score);
            return (
              <div key={dimension.name}>
                <div className="flex items-baseline justify-between text-sm">
                  <span className="font-medium">
                    {dimension.name}{" "}
                    <span className="text-xs font-normal text-gray-500">
                      {dimension.type === "blocker" ? "blocker" : "accelerator"}
                    </span>
                  </span>
                  <span className={`font-semibold ${dimensionTone.text}`}>
                    {dimension.score}
                    <span className="text-xs text-gray-500">/10</span>
                  </span>
                </div>
                <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-gray-200">
                  <div className={`h-full ${dimensionTone.bar}`} style={{ width: `${dimension.score * 10}%` }} />
                </div>
                <p className="mt-1.5 text-sm text-gray-600">{dimension.diagnosis}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
