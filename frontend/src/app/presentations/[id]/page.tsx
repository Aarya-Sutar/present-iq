"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import { usePopup } from "@/components/popup";
import api from "@/lib/api";

type Presentation = {
  id: number;
  case_prompt: string;
  domain_type: string;
  evaluation_rubric: Record<string, unknown>;
  original_filename: string;
  processing_status: string;
};

type FrameworkMatch = {
  framework: string;
  score: number;
  semantic_score: number;
  keyword_score: number;
  title_score: number;
  method: string;
  evidence: string[];
  reference_text: string | null;
};

type Slide = {
  id: number;
  presentation_id: number;
  slide_number: number;
  slide_title: string | null;
  extracted_text: string;
  ocr_text: string;
  image_paths: string[];
  slide_metadata: Record<string, unknown>;
  slide_category: string | null;
  classification_confidence: number | null;
  classification_reason: string | null;
  primary_framework: string | null;
  framework_confidence: number | null;
  framework_reason: string | null;
  framework_matches: FrameworkMatch[];
  created_at: string;
};

type Analysis = {
  id: number;
  presentation_id: number;
  analysis_status: string;
  business_logic_score: number | null;
  strategy_strength_score: number | null;
  analytical_depth_score: number | null;
  financial_soundness_score: number | null;
  communication_clarity_score: number | null;
  framework_utilization_score: number | null;
  overall_presentation_quality_score: number | null;
  score_breakdown: Record<string, unknown>;
  strengths: string[];
  weaknesses: string[];
  missing_elements: string[];
  recommendations: string[];
  investor_questions: string[];
  executive_summary: string | null;
  consultant_feedback: string | null;
  model_name: string | null;
  created_at: string;
  updated_at: string;
  prompt_alignment_score: number | null;
  evidence_grounding_score: number | null;
  slide_insights: {
    slide_number: number;
    slide_title: string | null;
    slide_category: string | null;
    key_claim: string;
    evidence_status: string;
    evidence_markers: string[];
    risk_flags: string[];
    reasoning_note: string;
  }[];
  unsupported_claims: string[];
  reasoning_gaps: string[];
};
type Report = {
  id: number;
  presentation_id: number;
  report_status: string;
  report_filename: string | null;
  report_file_path: string | null;
  report_summary: string | null;
  error_message: string | null;
  generated_at: string | null;
  created_at: string;
  updated_at: string;
};

export default function PresentationSlidesPage() {
  const params = useParams();
  const { notify } = usePopup();
  const presentationId = params.id as string;
  const [presentation, setPresentation] = useState<Presentation | null>(null);
  const [slides, setSlides] = useState<Slide[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loadingPresentation, setLoadingPresentation] = useState(true);
  const [loadingSlides, setLoadingSlides] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(true);
  const [queueing, setQueueing] = useState(false);
  const [report, setReport] = useState<Report | null>(null);
  const reportStatus = (report?.report_status || "").toLowerCase();
  const reportBusy = reportStatus === "queued" || reportStatus === "processing";
  const reportReady = reportStatus === "completed";
  const [loadingReport, setLoadingReport] = useState(true);
  const [queueingReport, setQueueingReport] = useState(false);
  const promptBrief = String(analysis?.score_breakdown?.prompt_brief ?? "");
  const problemStatement = String(
    analysis?.score_breakdown?.problem_statement ?? "",
  );
  const expectedFocusAreas = Array.isArray(
    analysis?.score_breakdown?.expected_focus_areas,
  )
    ? (analysis?.score_breakdown?.expected_focus_areas as string[])
    : [];
  const evaluationCriteria = Array.isArray(
    analysis?.score_breakdown?.evaluation_criteria,
  )
    ? (analysis?.score_breakdown?.evaluation_criteria as string[])
    : [];

  const analysisStatus = (analysis?.analysis_status || "").toLowerCase();

  const analysisBusy =
    analysisStatus === "queued" || analysisStatus === "processing";

  const analysisReady = analysisStatus === "completed";

  const fetchPresentation = async () => {
    try {
      const response = await api.get(`/presentations/${presentationId}`);
      setPresentation(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoadingPresentation(false);
    }
  };

  const fetchSlides = async () => {
    try {
      const response = await api.get(`/presentations/${presentationId}/slides`);
      setSlides(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoadingSlides(false);
    }
  };

  const fetchAnalysis = async () => {
    try {
      const response = await api.get(
        `/presentations/${presentationId}/analysis`,
      );
      setAnalysis(response.data);
    } catch (error) {
      setAnalysis(null);
    } finally {
      setLoadingAnalysis(false);
    }
  };
  const fetchReport = async () => {
    try {
      const response = await api.get(`/presentations/${presentationId}/report`);
      setReport(response.data);
    } catch (error) {
      setReport(null);
    } finally {
      setLoadingReport(false);
    }
  };

  useEffect(() => {
    if (!presentationId) return;
    fetchPresentation();
    fetchSlides();
    fetchAnalysis();
    fetchReport();
  }, [presentationId]);

  useEffect(() => {
    const status = analysis?.analysis_status;
    if (status !== "queued" && status !== "processing") {
      return;
    }

    const interval = setInterval(() => {
      fetchAnalysis();
    }, 5000);

    return () => clearInterval(interval);
  }, [analysis?.analysis_status, presentationId]);

  useEffect(() => {
    const status = report?.report_status;
    if (status !== "queued" && status !== "processing") {
      return;
    }

    const interval = setInterval(() => {
      fetchReport();
    }, 5000);

    return () => clearInterval(interval);
  }, [report?.report_status, presentationId]);

  const handleGenerateAnalysis = async () => {
    try {
      setQueueing(true);
      await api.post(`/presentations/${presentationId}/analysis/generate`);
      await fetchAnalysis();
    } catch (error) {
      console.error(error);
      await notify({
        title: "Analysis queue failed",
        message: "The analysis job could not be started.",
        tone: "danger",
        confirmLabel: "OK",
      });
    } finally {
      setQueueing(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setQueueingReport(true);
      await api.post(`/presentations/${presentationId}/report/generate`);
      await fetchReport();
    } catch (error) {
      console.error(error);
      await notify({
        title: "Report queue failed",
        message: "The report job could not be started.",
        tone: "danger",
        confirmLabel: "OK",
      });
    } finally {
      setQueueingReport(false);
    }
  };
  const handleDownloadReport = async () => {
    try {
      const token = localStorage.getItem("token");

      console.log("TOKEN:", token);

      const response = await fetch(
        `http://localhost:8000/api/v1/presentations/${presentationId}/report/download`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      console.log("STATUS:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.log("ERROR RESPONSE:", errorText);

        throw new Error(`Download failed: ${response.status}`);
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `DeckLens_Report_${presentationId}.pdf`;

      document.body.appendChild(a);
      a.click();

      a.remove();

      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      await notify({
        title: "Download failed",
        message: "The PDF report could not be downloaded.",
        tone: "danger",
        confirmLabel: "OK",
      });
    }
  };
  const scoreCards = useMemo(() => {
    if (!analysis) return [];

    return [
      ["Business Logic", analysis.business_logic_score],
      ["Strategy Strength", analysis.strategy_strength_score],
      ["Analytical Depth", analysis.analytical_depth_score],
      ["Financial Soundness", analysis.financial_soundness_score],
      ["Clarity", analysis.communication_clarity_score],
      ["Framework Utilization", analysis.framework_utilization_score],
      ["Prompt Alignment", analysis.prompt_alignment_score],
      ["Evidence Grounding", analysis.evidence_grounding_score],
      ["Overall", analysis.overall_presentation_quality_score],
    ].map(([label, value]) => ({
      label,
      value,
    }));
  }, [analysis]);

  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold">Contextual Evaluation</h1>
            <p className="mt-2 text-sm text-zinc-400">
              Presentation ID: {presentationId}
            </p>
          </div>

          <button
            onClick={handleGenerateAnalysis}
            disabled={queueing || analysisBusy || analysisReady}
            className="
                rounded-lg
                bg-white
                px-4
                py-2
                text-sm
                font-medium
                text-black
                transition
                hover:bg-zinc-200
                cursor-pointer
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
          >
            {queueing
              ? "Queueing Analysis..."
              : analysisBusy
                ? "Generating..."
                : analysisReady
                  ? "Analysis Complete"
                  : "Generate Analysis"}
          </button>
        </div>

        <section className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
          <h2 className="text-xl font-semibold">Case Context</h2>

          {loadingPresentation ? (
            <p className="mt-4 text-zinc-400">Loading case context...</p>
          ) : presentation ? (
            <div className="mt-4 space-y-3 text-sm text-zinc-300">
              <p>
                <span className="font-medium text-white">File:</span>{" "}
                {presentation.original_filename}
              </p>
              <p>
                <span className="font-medium text-white">Domain:</span>{" "}
                {presentation.domain_type}
              </p>
              <p className="whitespace-pre-wrap">
                <span className="font-medium text-white">Case Prompt:</span>{" "}
                {presentation.case_prompt}
              </p>
              <p className="whitespace-pre-wrap">
                <span className="font-medium text-white">Rubric:</span>{" "}
                {Object.keys(presentation.evaluation_rubric || {}).length > 0
                  ? JSON.stringify(presentation.evaluation_rubric, null, 2)
                  : "No rubric provided"}
              </p>
            </div>
          ) : (
            <p className="mt-4 text-zinc-400">Case context not found.</p>
          )}
        </section>

        <section className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
          <h2 className="text-xl font-semibold">Prompt Breakdown</h2>

          <div className="mt-4 space-y-3 text-sm text-zinc-300">
            <p className="whitespace-pre-wrap">
              <span className="font-medium text-white">Brief:</span>{" "}
              {promptBrief || "No prompt brief available."}
            </p>

            <p className="whitespace-pre-wrap">
              <span className="font-medium text-white">Problem Statement:</span>{" "}
              {problemStatement || "N/A"}
            </p>

            <div>
              <p className="font-medium text-white">Expected Focus Areas</p>
              <p className="mt-1">
                {expectedFocusAreas.length > 0
                  ? expectedFocusAreas.join(", ")
                  : "None"}
              </p>
            </div>

            <div>
              <p className="font-medium text-white">Evaluation Criteria</p>
              <p className="mt-1">
                {evaluationCriteria.length > 0
                  ? evaluationCriteria.join(", ")
                  : "None"}
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold">Report</h2>
            <span className="rounded-full border border-zinc-700 px-3 py-1 text-xs uppercase tracking-wide text-zinc-300">
              {report?.report_status || "not generated"}
            </span>
          </div>

          {loadingReport ? (
            <p className="mt-4 text-zinc-400">Loading report status...</p>
          ) : (
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                onClick={handleGenerateReport}
                disabled={queueingReport || reportBusy || reportReady}
                className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-zinc-200 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
              >
                {queueingReport
                  ? "Queuing Report..."
                  : reportBusy
                    ? "Generating..."
                    : reportReady
                      ? "Report Ready"
                      : "Generate Report"}
              </button>

              {reportReady && (
                <button
                  onClick={handleDownloadReport}
                  className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-white transition hover:bg-zinc-800 cursor-pointer"
                >
                  Download PDF
                </button>
              )}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold">Scorecard</h2>
            <span className="rounded-full border border-zinc-700 px-3 py-1 text-xs uppercase tracking-wide text-zinc-300">
              {analysis?.analysis_status || "not started"}
            </span>
          </div>

          {loadingAnalysis ? (
            <p className="mt-4 text-zinc-400">Loading analysis...</p>
          ) : analysis ? (
            <div className="mt-5 space-y-5">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {scoreCards.map((card) => (
                  <div
                    key={card.label}
                    className="rounded-xl border border-zinc-800 bg-zinc-950 p-4"
                  >
                    <p className="text-sm text-zinc-400">{card.label}</p>
                    <p className="mt-2 text-2xl font-semibold">
                      {typeof card.value == "number" &&
                        card.value !== null &&
                        card.value !== undefined
                        ? `${Math.round(card.value)}`
                        : "N/A"}
                    </p>
                  </div>
                ))}
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Executive Summary</h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-300">
                    {analysis.executive_summary || "No summary yet."}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Consultant Feedback</h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-300">
                    {analysis.consultant_feedback || "No feedback yet."}
                  </p>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Slide Reasoning Notes</h3>

                  <div className="mt-3 space-y-2 text-sm text-zinc-300">
                    {analysis.slide_insights.length > 0 ? (
                      analysis.slide_insights.slice(0, 8).map((item) => (
                        <div
                          key={item.slide_number}
                          className="rounded-lg border border-zinc-800 p-3"
                        >
                          <p className="font-medium text-white">
                            Slide {item.slide_number}
                            {item.slide_title ? ` - ${item.slide_title}` : ""}
                          </p>

                          <p className="mt-2 text-zinc-300">
                            {item.reasoning_note}
                          </p>

                          {item.risk_flags.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {item.risk_flags.map((flag) => (
                                <span
                                  key={flag}
                                  className="rounded-full border border-red-800 px-2 py-1 text-xs text-red-300"
                                >
                                  {flag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <p>No reasoning notes available.</p>
                    )}
                  </div>
                </div>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                <h3 className="font-medium">Reasoning Audit</h3>
                <div className="mt-3 space-y-3 text-sm text-zinc-300">
                  <div>
                    <p className="font-medium text-white">Reasoning Gaps</p>
                    <ul className="mt-2 space-y-1">
                      {analysis.reasoning_gaps.length > 0 ? (
                        analysis.reasoning_gaps.map((item) => (
                          <li key={item}>• {item}</li>
                        ))
                      ) : (
                        <li>• None</li>
                      )}
                    </ul>
                  </div>

                  <div>
                    <p className="font-medium text-white">Unsupported Claims</p>
                    <ul className="mt-2 space-y-1">
                      {analysis.unsupported_claims.length > 0 ? (
                        analysis.unsupported_claims.map((item) => (
                          <li key={item}>• {item}</li>
                        ))
                      ) : (
                        <li>• None</li>
                      )}
                    </ul>
                  </div>
                  {analysis.slide_insights.length > 0 && (
                    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                      <h3 className="font-medium">Slide Reasoning Notes</h3>
                      <div className="mt-3 space-y-2 text-sm text-zinc-300">
                        {analysis.slide_insights.slice(0, 8).map((item) => (
                          <div
                            key={item.slide_number}
                            className="rounded-lg border border-zinc-800 p-3"
                          >
                            <p className="font-medium text-white">
                              Slide {item.slide_number}{" "}
                              {item.slide_title ? `- ${item.slide_title}` : ""}
                            </p>
                            <p className="mt-1">{item.reasoning_note}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="grid gap-4 lg:grid-cols-3">
                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Strengths</h3>
                  <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                    {analysis.strengths.length > 0 ? (
                      analysis.strengths.map((item) => (
                        <li key={item}>• {item}</li>
                      ))
                    ) : (
                      <li>• None</li>
                    )}
                  </ul>
                </div>

                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Weaknesses</h3>
                  <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                    {analysis.weaknesses.length > 0 ? (
                      analysis.weaknesses.map((item) => (
                        <li key={item}>• {item}</li>
                      ))
                    ) : (
                      <li>• None</li>
                    )}
                  </ul>
                </div>

                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Missing Elements</h3>
                  <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                    {analysis.missing_elements.length > 0 ? (
                      analysis.missing_elements.map((item) => (
                        <li key={item}>• {item}</li>
                      ))
                    ) : (
                      <li>• None</li>
                    )}
                  </ul>
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Recommendations</h3>
                  <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                    {analysis.recommendations.length > 0 ? (
                      analysis.recommendations.map((item) => (
                        <li key={item}>• {item}</li>
                      ))
                    ) : (
                      <li>• None</li>
                    )}
                  </ul>
                </div>

                <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="font-medium">Investor Questions</h3>
                  <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                    {analysis.investor_questions.length > 0 ? (
                      analysis.investor_questions.map((item) => (
                        <li key={item}>• {item}</li>
                      ))
                    ) : (
                      <li>• None</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-zinc-400">
              No analysis yet. Generate one after slide extraction.
            </p>
          )}
        </section>

        <section>
          {loadingSlides ? (
            <p className="text-zinc-400">Loading slides...</p>
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
                  <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h2 className="text-lg font-medium">
                        Slide {slide.slide_number}
                      </h2>
                      <p className="text-sm text-zinc-400">
                        {slide.slide_title || "Untitled slide"}
                      </p>
                    </div>

                    <div className="rounded-full border border-zinc-700 px-3 py-1 text-xs uppercase tracking-wide text-zinc-300">
                      {slide.slide_category || "Unclassified"}
                    </div>
                  </div>

                  <div className="mb-4 space-y-2 text-sm text-zinc-400">
                    <div>
                      Confidence:{" "}
                      {slide.classification_confidence !== null
                        ? `${Math.round(slide.classification_confidence * 100)}%`
                        : "N/A"}
                      {slide.classification_reason
                        ? ` • Reason: ${slide.classification_reason}`
                        : ""}
                    </div>

                    <div>
                      Primary framework:{" "}
                      {slide.primary_framework || "None detected"}
                      {slide.framework_confidence !== null
                        ? ` • ${Math.round(slide.framework_confidence * 100)}%`
                        : ""}
                      {slide.framework_reason
                        ? ` • Reason: ${slide.framework_reason}`
                        : ""}
                    </div>
                  </div>

                  {slide.framework_matches.length > 0 && (
                    <div className="mb-4">
                      <p className="mb-2 font-medium text-white">
                        Detected Frameworks
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {slide.framework_matches.map((framework) => (
                          <span
                            key={framework.framework}
                            className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-200"
                          >
                            {framework.framework} •{" "}
                            {Math.round(framework.score * 100)}%
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="space-y-4 text-sm text-zinc-300">
                    <div>
                      <p className="mb-1 font-medium text-white">
                        Extracted Text
                      </p>
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
        </section>
      </div>
    </main>
  );
}
