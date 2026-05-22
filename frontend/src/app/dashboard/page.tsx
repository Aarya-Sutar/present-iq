"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import api from "@/lib/api";

type Presentation = {
  id: number;
  original_filename: string;
  file_type: string;
  file_size_bytes: number | null;
  processing_status: string;
  created_at: string;
};

export default function DashboardPage() {
  const [presentations, setPresentations] = useState<Presentation[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const fetchPresentations = async () => {
    try {
      const response = await api.get("/presentations");
      setPresentations(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPresentations();
  }, []);

  const handleExtract = async (presentationId: number) => {
    try {
      setBusyId(presentationId);
      await api.post(`/presentations/${presentationId}/extract`);
      await fetchPresentations();
      alert("Extraction completed");
    } catch (error) {
      console.error(error);
      alert("Extraction failed");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Dashboard</h1>
            <p className="mt-2 text-sm text-zinc-400">
              Uploaded presentations and slide extraction status
            </p>
          </div>

          <Link
            href="/upload"
            className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-black"
          >
            Upload
          </Link>
        </div>

        {loading ? (
          <p className="text-zinc-400">Loading...</p>
        ) : presentations.length === 0 ? (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-400">
            No presentations uploaded yet.
          </div>
        ) : (
          <div className="grid gap-4">
            {presentations.map((presentation) => (
              <div
                key={presentation.id}
                className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <h2 className="text-lg font-medium">
                      {presentation.original_filename}
                    </h2>
                    <p className="text-sm text-zinc-400">
                      Type: {presentation.file_type}
                      {presentation.file_size_bytes
                        ? ` • ${Math.round(presentation.file_size_bytes / 1024)} KB`
                        : ""}
                    </p>
                    <p className="text-sm text-zinc-400">
                      Status: {presentation.processing_status}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <button
                      onClick={() => handleExtract(presentation.id)}
                      disabled={busyId === presentation.id}
                      className="rounded-lg border border-zinc-700 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {busyId === presentation.id
                        ? "Extracting..."
                        : "Extract Slides"}
                    </button>

                    <Link
                      href={`/presentations/${presentation.id}`}
                      className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-black"
                    >
                      View Slides
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}