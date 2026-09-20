export function CtaBanner({ cta }: { cta: { text: string; url: string } | null }) {
  if (!cta) return null;

  return (
    <section className="rounded-lg border border-gray-300 bg-white p-6 text-center print-break-inside-avoid">
      <p className="text-base font-medium text-gray-900">{cta.text}</p>
      <a
        href={cta.url}
        className="mt-4 inline-block rounded-md bg-gray-900 px-5 py-2.5 text-sm font-medium text-white"
        rel="noopener noreferrer"
      >
        {cta.url.replace(/^https?:\/\//, "")}
      </a>
    </section>
  );
}
