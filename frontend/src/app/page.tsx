import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-6xl space-y-10">
        <section className="grid gap-8 rounded-3xl border border-zinc-800 bg-zinc-900 p-8 lg:grid-cols-[1.5fr_1fr] lg:p-10">
          <div className="space-y-5">
            <p className="text-sm uppercase tracking-[0.3em] text-zinc-400">
              Contextual deck evaluator
            </p>
            <h1 className="max-w-2xl text-4xl font-semibold leading-tight">
              Evaluate business presentations against the actual case prompt, not against a generic template.
            </h1>
            <p className="max-w-2xl text-zinc-300">
              Upload a PPT or PDF, attach the task prompt, generate a structured analysis, inspect reasoning gaps, and export a report.
            </p>

            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                href="/upload"
                className="rounded-full bg-white px-5 py-3 font-medium text-black transition hover:bg-zinc-200 cursor-pointer"
              >
                Upload deck
              </Link>
              <Link
                href="/dashboard"
                className="rounded-full border border-zinc-700 px-5 py-3 font-medium text-white transition hover:bg-zinc-800 cursor-pointer"
              >
                Open dashboard
              </Link>
            </div>
          </div>

          <div className="grid gap-4 rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
            <div>
              <p className="text-sm text-zinc-400">What it does</p>
              <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                <li>• Parses slides and OCR text</li>
                <li>• Detects frameworks semantically</li>
                <li>• Scores prompt alignment and evidence grounding</li>
                <li>• Generates consultant-style feedback</li>
                <li>• Exports a PDF report</li>
              </ul>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
              <p className="text-sm font-medium text-white">Best for</p>
              <p className="mt-2 text-sm text-zinc-300">
                E-Cell inductions, case reviews, startup pitches, consulting practice, and operations challenges.
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <h2 className="text-lg font-semibold">Upload</h2>
            <p className="mt-2 text-sm text-zinc-400">
              Attach the deck and the case prompt.
            </p>
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <h2 className="text-lg font-semibold">Analyze</h2>
            <p className="mt-2 text-sm text-zinc-400">
              Review category detection, frameworks, scores, and reasoning.
            </p>
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <h2 className="text-lg font-semibold">Export</h2>
            <p className="mt-2 text-sm text-zinc-400">
              Generate a PDF report for mentors or judges.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}