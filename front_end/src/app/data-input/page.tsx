"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/navbar";
import{
  getDatasets,
  uploadDataset,
  getTruncatedDataset,
  deleteDataset,
} from "@/lib/api";

interface UploadedFile {
  name: string;
  datasetId: string;
  head: any[];
}

const DataInputPage: React.FC = () => {
  const router = useRouter();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loadingList, setLoadingList] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

/* ----------------------------- LOAD DATASETS ----------------------------- */
  useEffect(() => {
    (async () => {
      try {
        setLoadingList(true);
        const data = await getDatasets();

        const formatted = data.map((d: any) => ({
          name: d.original_filename,
          datasetId: d.id,
          head: d.head || [],
        }));

        setFiles(formatted);
      } catch (err) {
        console.error("Error loading datasets:", err);
      } finally {
        setLoadingList(false);
      }
    })();
  }, []);

  /* ----------------------------- UPLOAD NEW FILE ----------------------------- */
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const data = await uploadDataset(file);
      const newFile = {
        name: file.name,
        datasetId: data.dataset_id,
        head: [],
      };
      setFiles((prev) => [...prev, newFile]);
    } catch (err) {
      console.error("Upload failed:", err);
      alert("File upload failed.");
    } finally {
      setUploading(false);
    }
  };

/* ----------------------------- SELECT FILE ----------------------------- */
  const handleSelectFile = async (file: UploadedFile) => {
    try {
      console.log(file.datasetId);
      const data = await getTruncatedDataset(file.datasetId);
      const updated = { ...file, head: data.head || [] };
      setSelectedFile(updated);
    } catch (err) {
      console.error("Failed to fetch preview:", err);
      setSelectedFile(file);
    }
  };

  /* ----------------------------- DELETE FILE ----------------------------- */
  const handleDeleteFile = async (datasetId: string) => {
    if (!confirm("Are you sure you want to delete this dataset?")) return;

    // Optimistic UI update
    setFiles((prev) => prev.filter((f) => f.datasetId !== datasetId));

    // If the selected file was deleted, clear it
    if (selectedFile?.datasetId === datasetId) setSelectedFile(null);

    try {
      await deleteDataset(datasetId);
    } catch (err) {
      console.error("Failed to delete dataset:", err);
      alert("Failed to delete dataset. Please try again.");
      // Optionally: refetch datasets if deletion failed
    }
  };

  /* ----------------------------- CONFIRM SELECTION ----------------------------- */
  const handleConfirmSelection = () => {
    if (!selectedFile) return;
    router.push(`/graph-edit?dataset_id=${selectedFile.datasetId}`);
  };

  /* ----------------------------- RENDER ----------------------------- */
  return (
    <div className="flex flex-col h-screen bg-blue-50">
      <Navbar />
      <div className="flex flex-1 p-4 gap-4">
        {/* Left Panel */}
        <div className="w-1/4 bg-blue-100 rounded-xl p-4 flex flex-col border border-blue-200">
          <h2 className="font-semibold text-gray-700 mb-4">Uploaded Files</h2>

          <div className="flex flex-col gap-2 mb-4 overflow-y-auto">
            {loadingList ? (
              <p className="text-gray-500 text-sm">Loading...</p>
            ) : files.length === 0 ? (
              <p className="text-gray-500 text-sm">No files uploaded yet.</p>
            ) : (
              files.map((file) => (
                <div
                  key={file.datasetId}
                  className={`relative group border rounded-md p-2 cursor-pointer ${
                    selectedFile?.datasetId === file.datasetId
                      ? "bg-green-100 border-green-400"
                      : "bg-white hover:bg-gray-50"
                  }`}
                  onMouseEnter={() => setHoveredId(file.datasetId)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteFile(file.datasetId);
                    }}
                    className={`absolute top-1 right-1 text-gray-400 hover:text-red-500 transition-opacity ${
                      hoveredId === file.datasetId ? "opacity-100" : "opacity-0"
                    }`}
                    title="Delete dataset"
                  >
                    ✕
                  </button>
                  <div onClick={() => handleSelectFile(file)}>{file.name}</div>
                </div>
              ))
            )}
          </div>

          <div className="border-t pt-3 mt-auto">
            <p className="text-sm text-gray-600 mb-2">Upload new file</p>
            <label className="block border border-gray-300 rounded-md bg-gray-100 p-3 text-center cursor-pointer hover:bg-gray-200">
              {uploading ? "Uploading..." : "Select CSV file"}
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Right Panel */}
        <div className="flex-1 bg-blue-100 rounded-xl border border-blue-200 flex flex-col p-4">
          <div className="bg-white rounded-lg border border-gray-200 overflow-auto flex-1">
            {selectedFile ? (
              selectedFile.head && selectedFile.head.length > 0 ? (
                <table className="min-w-full text-sm text-left">
                  <thead className="bg-gray-100 border-b">
                    <tr>
                      {Object.keys(selectedFile.head[0]).map((header, idx) => (
                        <th key={idx} className="px-3 py-2 font-semibold">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {selectedFile.head.map((row, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        {Object.keys(row).map((col, cIdx) => (
                          <td key={cIdx} className="px-3 py-2">
                            {row[col]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  No preview available for this file.
                </div>
              )
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                Select a file to preview its contents.
              </div>
            )}
          </div>

          <button
            disabled={!selectedFile}
            onClick={handleConfirmSelection}
            className={`mt-4 self-end px-6 py-2 rounded-md text-white font-medium transition ${
              selectedFile
                ? "bg-blue-600 hover:bg-blue-700"
                : "bg-gray-300 cursor-not-allowed"
            }`}
          >
            Confirm Selection →
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataInputPage;