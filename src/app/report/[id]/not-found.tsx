export default function ReportNotFound() {
  return (
    <main className="mx-auto max-w-lg px-6 py-24 text-center">
      <h1 className="text-xl font-semibold text-gray-900">Report not found</h1>
      <p className="mt-3 text-sm text-gray-600">
        This link does not point at a saved audit. Check the link you were sent.
      </p>
    </main>
  );
}
