"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/navbar";

interface Analysis {
  id: string;
  dataset_id: string;
  status: string;
  execution_log?: any[];
  artifacts?: Record<string, any>;
  error?: string;
  created_at?: string;
  finished_at?: string;
}

interface DataFrameRow {
  [key: string]: any;
}

const API_BASE = "http://127.0.0.1:8000";
const MAX_CELL_CHARS = 200;

const truncate = (value: any) => {
  if (typeof value === "string" && value.length > MAX_CELL_CHARS) {
    return value.slice(0, MAX_CELL_CHARS).replace(/\s+\S*$/, "") + "...";
  }
  return value;
};

const InsightVisualizerPage: React.FC = () => {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);
  const [dataFrames, setDataFrames] = useState<{ key: string; df: DataFrameRow[] }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [downloading, setDownloading] = useState(false);
  const [datasets, setDatasets] = useState<Record<string, string>>({});

  // 🔹 Full-page loading overlay (independent spinner)
  const LoadingSpinner = () => (
  <div className="flex flex-col items-center justify-center mt-8 text-blue-700">
    <svg
      className="animate-spin h-6 w-6 text-blue-600 mb-2"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      ></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8H4z"
      ></path>
    </svg>
    <span className="text-sm font-medium tracking-wide">Loading analysis data…</span>
  </div>
);


  // 🔹 Initial fetch for analyses + datasets
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [analysesRes, datasetsRes] = await Promise.all([
          fetch(`${API_BASE}/analyses`),
          fetch(`${API_BASE}/datasets`),
        ]);
        if (!analysesRes.ok || !datasetsRes.ok) throw new Error("Failed to fetch data");

        const analysesData = await analysesRes.json();
        const datasetsData = await datasetsRes.json();

        const datasetMap: Record<string, string> = {};
        datasetsData.forEach((ds: any) => {
          datasetMap[ds.id] = ds.original_filename || ds.id;
        });

        setDatasets(datasetMap);
        setAnalyses(analysesData);
      } catch (err: any) {
        setError(err.message || "Error loading analyses");
      }
    };
    fetchAll();
  }, []);

  // 🔹 Poll backend every 5 seconds to refresh analysis statuses
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/analyses`);
        if (!res.ok) throw new Error("Failed to fetch analyses");
        const updated: Analysis[] = await res.json();
        setAnalyses(updated);

        // ✅ Update selected analysis if its status changes
        if (selectedAnalysis) {
          const refreshed = updated.find((a) => a.id === selectedAnalysis.id);
          if (refreshed && refreshed.status !== selectedAnalysis.status) {
            setSelectedAnalysis(refreshed);
          }
        }
      } catch (err) {
        console.error("Error refreshing analyses:", err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [selectedAnalysis]);


  // 🔹 Load artifacts for selected analysis
  const loadArtifacts = async (analysis: Analysis) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/analyses/${analysis.id}`);
      if (!res.ok) throw new Error("Failed to fetch analysis details");
      const detailedAnalysis: Analysis = await res.json();
      setSelectedAnalysis(detailedAnalysis);

      if (!detailedAnalysis.artifacts) {
        setDataFrames([]);
        return;
      }

      const dfPromises = Object.entries(detailedAnalysis.artifacts).map(
        async ([key]) => {
          const res = await fetch(
            `${API_BASE}/analyses/${detailedAnalysis.id}/artifacts/${key}?format=json&nrows=20`
          );
          if (!res.ok) throw new Error(`Failed to fetch artifact ${key}`);
          const df = await res.json();

          const truncatedDf = df.map((row: Record<string, any>) => {
            const newRow: Record<string, any> = {};
            Object.entries(row).forEach(([k, v]) => {
              newRow[k] = truncate(v);
            });
            return newRow;
          });

          return { key, df: truncatedDf };
        }
      );

      const dfs = await Promise.all(dfPromises);
      setDataFrames(dfs);

      const initialCollapsed: Record<string, boolean> = {};
      dfs.forEach(({ key }) => (initialCollapsed[key] = true));
      setCollapsed(initialCollapsed);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Error loading artifacts");
      setDataFrames([]);
    } finally {
      // Small delay for smoother fade-out
      setTimeout(() => setLoading(false), 300);
    }
  };

  const toggleCollapse = (key: string) => {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleDownloadAllCSVs = async () => {
    if (!selectedAnalysis || !selectedAnalysis.artifacts) return;
    setDownloading(true);

    try {
      const artifactKeys = Object.keys(selectedAnalysis.artifacts);
      for (const key of artifactKeys) {
        const url = `${API_BASE}/analyses/${selectedAnalysis.id}/artifacts/${key}?format=csv`;
        const res = await fetch(url);
        if (!res.ok) {
          console.error(`Failed to download ${key}`);
          continue;
        }
        const blob = await res.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${selectedAnalysis.id}_${key}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error("Error downloading CSVs:", err);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-blue-50 relative">
      <Navbar />

      {/* 🔹 Full-page overlay spinner */}
      {(loading || selectedAnalysis?.status === "running") && (
        <div className="absolute inset-0 flex justify-center items-center pointer-events-none z-40">
          <div className="bg-white/80 border border-blue-200 rounded-xl shadow-lg px-6 py-4">
            <div className="flex flex-col items-center text-blue-700">
              <svg
                className="animate-spin h-8 w-8 text-blue-600 mb-3"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                ></path>
              </svg>
              <span className="text-base font-medium tracking-wide">
                Loading analysis data…
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="min-h-screen bg-blue-50 text-gray-800 px-8 py-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-md p-6 mb-8 text-center border border-blue-100">
          <h1 className="text-3xl font-bold text-blue-900 mb-2">Insight Visualizer</h1>
          <p className="text-gray-600">
            Review analysis results, explore DataFrames, and download insights.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap justify-between items-center gap-4 mb-8">
          <div>
            <label className="block font-semibold text-gray-700 mb-1">
              Select an analysis:
            </label>
            <select
              size={10}
              className="p-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
              onChange={(e) => {
                const analysis = analyses.find((a) => a.id === e.target.value);
                if (analysis) loadArtifacts(analysis);
              }}
              value={selectedAnalysis?.id || ""}
            >
              <option value="" disabled>
                -- Choose an analysis --
              </option>
              {[...analyses]
                .sort(
                  (a, b) =>
                    new Date(b.created_at || 0).getTime() -
                    new Date(a.created_at || 0).getTime()
                )
                .map((a) => {
                  const datasetName = datasets[a.dataset_id] || a.dataset_id;
                  const createdAt = a.created_at
                    ? new Date(a.created_at).toLocaleString()
                    : "Unknown date";
                  const statusIcon =
                    a.status === "completed"
                      ? "✅"
                      : a.status === "failed"
                      ? "❌"
                      : a.status === "queued"
                      ? "⏳"
                      : "⚙️";
                  return (
                    <option key={a.id} value={a.id}>
                      {statusIcon} {datasetName} — {createdAt}
                    </option>
                  );
                })}
            </select>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleDownloadAllCSVs}
              disabled={!selectedAnalysis || downloading}
              className={`px-5 py-2.5 rounded-lg font-semibold text-white transition-all ${
                downloading
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-green-600 hover:bg-green-700"
              }`}
            >
              {downloading ? "Downloading..." : "⬇️ Download All CSVs"}
            </button>
          </div>
        </div>

        {error && <p className="text-red-600 mb-4">{error}</p>}

        {/* Artifacts */}
        <div className="space-y-6">
          {dataFrames.map(({ key, df }) => (
            <div
              key={key}
              className="bg-white rounded-2xl shadow-sm border border-blue-100 overflow-hidden transition hover:shadow-md"
            >
              <div
                className="bg-blue-100 px-5 py-3 flex justify-between items-center cursor-pointer"
                onClick={() => toggleCollapse(key)}
              >
                <h2 className="font-semibold text-blue-900">{key}</h2>
                <span className="text-gray-700">{collapsed[key] ? "▼" : "▲"}</span>
              </div>
              {!collapsed[key] && (
                <div className="p-5 overflow-x-auto">
                  {df.length === 0 ? (
                    <p className="text-gray-500">No data available</p>
                  ) : (
                    <table className="min-w-full border border-gray-300 text-sm">
                      <thead>
                        <tr className="bg-gray-100">
                          {Object.keys(df[0]).map((col) => (
                            <th
                              key={col}
                              className="border border-gray-300 px-3 py-2 text-left font-semibold text-gray-700"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {df.map((row, idx) => (
                          <tr
                            key={idx}
                            className={idx % 2 === 0 ? "bg-gray-50" : "bg-white"}
                          >
                            {Object.values(row).map((val, i) => (
                              <td key={i} className="border border-gray-300 px-3 py-2">
                                {val}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InsightVisualizerPage;
