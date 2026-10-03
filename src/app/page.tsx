import Link from "next/link";
import { PublicAnalyzer } from "@/components/public-analyzer";
import { getBookingUrl } from "@/lib/config";

export const dynamic = "force-dynamic";

// Placeholder copy throughout. Swap in the real wording before launch.
const BENEFITS = [
  { title: "More leads", body: "Turn more of your current visitors into inquiries." },
  { title: "Less friction", body: "Find what stops people between interested and done." },
  { title: "Lower cost per lead", body: "Same ad spend, more conversions." },
];

const PROOF = ["[Client logo]", "[Client logo]", "[Client logo]", "[Client logo]", "[Client logo]"];

export default function HomePage() {
  const bookingUrl = getBookingUrl();

  return (
    <div>
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
          <span className="font-semibold">Quincy Lou</span>
          {bookingUrl ? (
            <a
              href={bookingUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white"
            >
              Book a free review
            </a>
          ) : null}
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-5xl px-4 py-20 sm:px-6">
          <p className="text-sm font-medium text-gray-500">Conversion rate optimization</p>
          <h1 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
            Your traffic is fine. Your page might not be.
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-gray-600">
            Get a free score for any landing page and see what is holding it back, in about a minute.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href="#analyze" className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white">
              Analyze my page
            </a>
            <a href="#how" className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-900">
              How it works
            </a>
          </div>
        </section>

        <section id="how" className="border-y border-gray-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
            <h2 className="text-2xl font-semibold">What a better page gets you</h2>
            <div className="mt-8 grid gap-6 sm:grid-cols-3">
              {BENEFITS.map((benefit) => (
                <div key={benefit.title} className="rounded-lg border border-gray-200 p-5">
                  <h3 className="font-semibold">{benefit.title}</h3>
                  <p className="mt-2 text-sm text-gray-600">{benefit.body}</p>
                </div>
              ))}
            </div>
            <div className="mt-10 flex flex-wrap gap-3">
              {PROOF.map((item, index) => (
                <span key={index} className="rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-500">
                  {item}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section id="analyze" className="mx-auto max-w-2xl scroll-mt-16 px-4 py-16 sm:px-6">
          <h2 className="text-2xl font-semibold">Free page analysis</h2>
          <p className="mt-2 mb-6 text-sm text-gray-600">Three quick questions, then the score.</p>
          <PublicAnalyzer bookingUrl={bookingUrl} />
        </section>

        <section className="border-t border-gray-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
            <h2 className="text-2xl font-semibold">A free 30 minute review</h2>
            <p className="mt-2 max-w-2xl text-gray-600">
              A real person goes through your page with you and tells you what to change first.
            </p>
            <ul className="mt-6 space-y-2 text-sm text-gray-700">
              <li>✓ No obligation</li>
              <li>✓ 30 minutes</li>
              <li>✓ Reviewed by a person, not just software</li>
            </ul>
            {bookingUrl ? (
              <a
                href={bookingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-6 inline-block rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
              >
                Book your free review
              </a>
            ) : null}
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-4 py-8 text-sm text-gray-500 sm:px-6">
        <span>This analysis is AI-generated and for informational purposes.</span>
        <Link href="/dashboard" className="underline underline-offset-2">
          Team login
        </Link>
      </footer>
    </div>
  );
}
