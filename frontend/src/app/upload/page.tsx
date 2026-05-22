"use client";

import { useState } from "react";

import api from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      alert("Select a file first");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      await api.post("/presentations/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      alert("Upload successful");
      setFile(null);
    } catch (error) {
      console.error(error);
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-white">
      <div className="w-full max-w-xl space-y-5 rounded-2xl border border-zinc-800 bg-zinc-900 p-8">
        <div>
          <h1 className="text-3xl font-semibold">Upload Presentation</h1>
          <p className="mt-2 text-sm text-zinc-400">
            Supported formats: PPT, PPTX, PDF
          </p>
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