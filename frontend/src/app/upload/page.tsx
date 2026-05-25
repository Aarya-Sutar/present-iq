"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { usePopup } from "@/components/popup";
import api from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const { notify } = usePopup();
  const [file, setFile] = useState<File | null>(null);
  const [casePrompt, setCasePrompt] = useState("");
  const [evaluationRubric, setEvaluationRubric] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      await notify({
        title: "File required",
        message: "Select a PPT, PPTX, or PDF before uploading.",
        tone: "warning",
        confirmLabel: "OK",
      });
      return;
    }

    if (!casePrompt.trim()) {
      await notify({
        title: "Case prompt required",
        message: "Add the prompt or question the deck should answer.",
        tone: "warning",
        confirmLabel: "OK",
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("case_prompt", casePrompt.trim());

    if (evaluationRubric.trim()) {
      formData.append("evaluation_rubric", evaluationRubric.trim());
    }

    try {
      setLoading(true);
      await api.post("/presentations/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      await notify({
        title: "Upload successful",
        message: "Your presentation has been submitted and is now queued.",
        tone: "success",
        confirmLabel: "Open dashboard",
      });
      router.push("/dashboard");
    } catch (error) {
      console.error(error);
      await notify({
        title: "Upload failed",
        message: "The file could not be submitted. Please try again.",
        tone: "danger",
        confirmLabel: "Try again",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-white">
      <div className="w-full max-w-2xl space-y-5 rounded-2xl border border-zinc-800 bg-zinc-900 p-8">
        <div>
          <h1 className="text-3xl font-semibold">Upload Presentation</h1>
          <p className="mt-2 text-sm text-zinc-400">
            Upload the deck plus the task/question it should answer.
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm text-zinc-300">Case Prompt</label>
          <textarea
            value={casePrompt}
            onChange={(e) => setCasePrompt(e.target.value)}
            placeholder="Example: Improve inter-campus collaboration for students through a scalable platform."
            className="min-h-28 w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3 text-sm outline-none"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm text-zinc-300">Optional Rubric</label>
          <textarea
            value={evaluationRubric}
            onChange={(e) => setEvaluationRubric(e.target.value)}
            placeholder="Paste rubric text or JSON here. Example: Innovation, feasibility, execution, clarity..."
            className="min-h-28 w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3 text-sm outline-none"
          />
        </div>

        <input
          type="file"
          accept=".ppt,.pptx,.pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3"
        />

        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full rounded-lg bg-white p-3 font-medium text-black disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>
    </main>
  );
}