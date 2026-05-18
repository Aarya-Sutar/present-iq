export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-white">
      <div className="mx-auto max-w-2xl space-y-6 text-center">
        <p className="text-sm uppercase tracking-[0.3em] text-zinc-400">
          PresentIQ
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
          AI-powered business presentation analysis
        </h1>
        <p className="text-base leading-7 text-zinc-300 sm:text-lg">
          Upload decks, extract slide content, detect business frameworks, score strategic quality,
          and generate consultant-style feedback.
        </p>
      </div>
    </main>
  );
}