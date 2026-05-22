"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import api from "@/lib/api";

type Slide = {
  id: number;
  presentation_id: number;
  slide_number: number;
  slide_title: string | null;
  extracted_text: string;
  ocr_text: string;
  image_paths: string[];
  metadata: Record<string, unknown>;
  created_at: string;
};

export default function PresentationSlidesPage() {
  const params = useParams();
  const presentationId = params.id as string;

  const [slides, setSlides] = useState<Slide[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSlides = async () => {
      try {
        const response = await api.get(`/presentations/${presentationId}/slides`);
        setSlides(response.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    if (presentationId) {
      fetchSlides();
    }
  }, [presentationId]);

  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <h1 className="text-3xl font-semibold">Extracted Slides</h1>
          <p className="mt-2 text-sm text-zinc-400">
            Presentation ID: {presentationId}
          </p>
        </div>

        {loading ? (
          <p className="text-zinc-400">Loading...</p>
        ) : slides.length === 0 ? (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-400">
            No slides extracted yet.
          </div>
        ) : (
          <div className="space-y-4">
            {slides.map((slide) => (
              <div
                key={slide.id}
                className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5"
              >
                <div className="mb-3 flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-medium">
                      Slide {slide.slide_number}
                    </h2>
                    <p className="text-sm text-zinc-400">
                      {slide.slide_title || "Untitled slide"}
                    </p>
                  </div>
                </div>

                <div className="space-y-4 text-sm text-zinc-300">
                  <div>
                    <p className="mb-1 font-medium text-white">Extracted Text</p>
                    <pre className="whitespace-pre-wrap rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-zinc-300">
                      {slide.extracted_text || "No text extracted"}
                    </pre>
                  </div>

                  <div>
                    <p className="mb-1 font-medium text-white">OCR Text</p>
                    <pre className="whitespace-pre-wrap rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-zinc-300">
                      {slide.ocr_text || "No OCR text"}
                    </pre>
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