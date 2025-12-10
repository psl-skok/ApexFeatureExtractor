export const API_BASE = "http://127.0.0.1:8000";

export async function getProjects() {
  const res = await fetch(`${API_BASE}/projects`);
  return res.json();
}

// Fetch list of saved analyses
export async function getAnalyses() {
  const res = await fetch(`${API_BASE}/analyses`);
  if (!res.ok) throw new Error("Failed to fetch analyses");
  return res.json();
}

// Fetch preview of a dataset by ID (adjust endpoint if needed)
export async function getDatasetPreview(id: string) {
  const res = await fetch(`${API_BASE}/datasets/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch dataset preview for ${id}`);
  return res.json();
}

// Fetch the function registry dictionary
export async function getFunctionRegistry() {
  const res = await fetch(`${API_BASE}/functions`);
  if (!res.ok) throw new Error("Failed to fetch function registry");
  return res.json();
}

// Send path to compiler/run endpoint
export async function runCompiler(datasetId: string, pathRequest: any[]) {
  const res = await fetch(`${API_BASE}/compiler/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, path_request: pathRequest }),
  });
  if (!res.ok) throw new Error("Failed to run compiler");
  return res.json();
}


export async function get_saved_graphs() {
  const res = await fetch(`${API_BASE}/saved-graphs`);
  if (!res.ok) throw new Error("Failed to fetch saved graphs");
  return res.json();
}

export async function get_saved_graph(id: string) {
  const res = await fetch(`${API_BASE}/saved-graphs/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch graph ${id}`);
  return res.json();
}

export async function save_graph(name: string, path: any[]) {
  const res = await fetch(`${API_BASE}/saved-graphs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, path }),
  });
  if (!res.ok) throw new Error("Failed to save graph");
  return res.json();
}
/* ----------------------------- DATASETS ----------------------------- */

export async function getDatasets() {
  const res = await fetch(`${API_BASE}/datasets`);
  if (!res.ok) throw new Error("Failed to fetch datasets");
  return res.json();
}

export async function uploadDataset(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/datasets`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("File upload failed");
  return res.json();
}

export async function getTruncatedDataset(id: string) {
  const res = await fetch(`${API_BASE}/datasets/truncated/${id}`);
  console.log(res);  // This is optional for debugging
  if (!res.ok) throw new Error(`Failed to fetch truncated dataset for ${id}`);
  return res.json();  // Add this to return the parsed JSON
}
export async function deleteDataset(id: string) {
  const res = await fetch(`${API_BASE}/datasets/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete dataset ${id}`);
  return res.json();
}