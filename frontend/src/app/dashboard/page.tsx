"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { usePopup } from "@/components/popup";
import api from "@/lib/api";

type Presentation = {
  id: number;
  case_prompt: string;
  domain_type: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number | null;
  processing_status: string;
  analysis_status: string | null;
  report_status: string | null;
  created_at: string;
};

export default function DashboardPage() {
  const { notify, confirm } = usePopup();
  const [presentations, setPresentations] = useState<Presentation[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [deleteLoadingId, setDeleteLoadingId] = useState<number | null>(null);
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

    const interval = setInterval(() => {
      fetchPresentations();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleQueue = async (presentationId: number) => {
    try {
      setBusyId(presentationId);
      await api.post(`/presentations/${presentationId}/extract`);
      await fetchPresentations();
    } catch (error) {
      console.error(error);
      await notify({
        title: "Processing failed",
        message: "The presentation could not be queued for processing.",
        tone: "danger",
        confirmLabel: "OK",
      });
    } finally {
      setBusyId(null);
    }
  };
  const handleDelete = async (presentationId: number) => {
    const confirmed = await confirm({
      title: "Delete presentation?",
      message:
        "This will permanently remove the presentation, slides, and related results.",
      tone: "danger",
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
    });

    if (!confirmed) return;

    try {
      setDeleteLoadingId(presentationId);

      await api.delete(`/presentations/${presentationId}`);

      await fetchPresentations();
    } catch (error) {
      console.error(error);
      await notify({
        title: "Delete failed",
        message: "The presentation could not be removed right now.",
        tone: "danger",
        confirmLabel: "OK",
      });
    } finally {
      setDeleteLoadingId(null);
    }
  };

  const statusChip = (value: string | null) => {
    const status = (value || "unknown").toLowerCase();
    const style =
      status === "completed"
        ? "border-emerald-700 bg-emerald-950 text-emerald-300"
        : status === "processing" || status === "queued"
          ? "border-amber-700 bg-amber-950 text-amber-300"
          : status === "failed"
            ? "border-red-700 bg-red-950 text-red-300"
            : "border-zinc-700 bg-zinc-900 text-zinc-300";

    return (
      <span
        className={`rounded-full border px-3 py-1 text-xs uppercase tracking-wide ${style}`}
      >
        {status}
      </span>
    );
  };

  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Dashboard</h1>
            <p className="mt-2 text-sm text-zinc-400">
              Uploaded presentations, task prompts, and live processing state.
            </p>
          </div>

          <Link
            href="/upload"
            className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-zinc-200 cursor-pointer"
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
            {presentations.map((presentation) => {
              const processing = presentation.processing_status?.toLowerCase();
              const buttonLabel =
                processing === "completed"
                  ? "Completed"
                  : processing === "processing"
                    ? "Processing..."
                    : processing === "uploaded"
                      ? "Queue Processing"
                      : "Reprocess";

              const buttonDisabled =
                busyId === presentation.id ||
                processing === "processing" ||
                processing === "completed";

              return (
                <div
                  key={presentation.id}
                  className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 transition hover:border-zinc-700"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-lg font-semibold">
                          {presentation.original_filename}
                        </h2>
                        {statusChip(presentation.processing_status)}
                      </div>

                      <p className="text-sm text-zinc-400">
                        Domain: {presentation.domain_type}
                      </p>

                      <p className="max-w-3xl text-sm text-zinc-400">
                        {presentation.case_prompt.length > 140
                          ? `${presentation.case_prompt.slice(0, 140)}...`
                          : presentation.case_prompt}
                      </p>
                    </div>

                    <div className="flex shrink-0 flex-nowrap items-center gap-3 self-start lg:self-auto">
                      <button
                        onClick={() => handleQueue(presentation.id)}
                        disabled={buttonDisabled}
                        className="whitespace-nowrap rounded-lg border border-zinc-700 px-4 py-2 text-sm transition hover:bg-zinc-800 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {busyId === presentation.id
                          ? "Queueing..."
                          : buttonLabel}
                      </button>

                      <Link
                        href={`/presentations/${presentation.id}`}
                        className="whitespace-nowrap rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-zinc-200 cursor-pointer"
                      >
                        View Slides
                      </Link>
                      <button
                        onClick={() => handleDelete(presentation.id)}
                        disabled={deleteLoadingId === presentation.id}
                        className="whitespace-nowrap rounded-lg border border-red-800 px-4 py-2 text-sm text-red-300 transition hover:bg-red-950 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {deleteLoadingId === presentation.id
                          ? "Deleting..."
                          : "Delete"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
