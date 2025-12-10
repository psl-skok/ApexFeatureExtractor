"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

// Define type for a path step (matches backend structure)
interface PathStep {
  function: string;
  args: Record<string, any>;
  input_df_name: string;
  output_df_name: string;
}

// Import API functions
import { getAnalyses, getDatasetPreview, getFunctionRegistry, runCompiler, get_saved_graphs, get_saved_graph, save_graph } from "../../lib/api";

// Extract inferEditor to module scope
const inferEditor = (a: any): { type: "text" | "number" | "boolean" | "list" | "dict"; itemType?: any; keyType?: any; valueType?: any } => {
  const t = (a?.type || "").toLowerCase();
  const def = a?.default;

  if (Array.isArray(def) || t.includes("list") || t.includes("array")) {
    let itemType = null;
    if (def?.length > 0) {
      itemType = inferEditor({ default: def[0] });
    } else if (t.includes("list[")) {
      const match = t.match(/list\[(.*)\]/);
      if (match) itemType = { type: match[1].toLowerCase() };
    }
    return { type: "list", itemType };
  }

  if (typeof def === "object" && def !== null && !Array.isArray(def) || t.includes("dict") || t.includes("mapping") || t.includes("json")) {
    let keyType = { type: "text" };
    let valueType = null;
    const entries = Object.entries(def || {});
    if (entries.length > 0) {
      valueType = inferEditor({ default: entries[0][1] });
    }
    return { type: "dict", keyType, valueType };
  }

  if (typeof def === "number" || t.includes("int") || t.includes("float") || t.includes("number")) return { type: "number" };
  if (typeof def === "boolean" || t.includes("bool")) return { type: "boolean" };
  return { type: "text" };
};

// Move interfaces here (before component)
interface ArgEditorProps {
  inferred: ReturnType<typeof inferEditor>;
  value: any;
  onChange: (newValue: any) => void;
  parentFunction?: string;  // New optional prop
  argName?: string;         // New optional prop
}

interface ListEditorProps {
  value: any[];
  inferred: { itemType?: ReturnType<typeof inferEditor> };
  onChange: (newValue: any[]) => void;
  parentFunction?: string;
  argName?: string;
}

interface DictEditorProps {
  value: Record<string, any>;
  inferred: { keyType?: ReturnType<typeof inferEditor>; valueType?: ReturnType<typeof inferEditor> };
  onChange: (newValue: Record<string, any>) => void;
  parentFunction?: string;
  argName?: string;
}

export default function GraphEditPage() {
  const [path, setPath] = useState<PathStep[]>([]); // Start with empty path
  const [graphType, setGraphType] = useState("sentiment");
  const [parameter, setParameter] = useState("duration");
  const [graphName, setGraphName] = useState("Untitled Graph");
  const [savedGraphs, setSavedGraphs] = useState<any[]>([]);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [datasetPreview, setDatasetPreview] = useState<any>(null);
  const [functionRegistry, setFunctionRegistry] = useState<Record<string, any>>({});

  const searchParams = useSearchParams();
  const datasetId = searchParams.get("dataset_id") || "";

  // Fetch data on load if datasetId present
  useEffect(() => {
    if (datasetId) {
      const fetchData = async () => {
        const results = await Promise.allSettled([
          getAnalyses(),
          getDatasetPreview(datasetId),
          getFunctionRegistry(),
          get_saved_graphs(),
        ]);

        const [analysesRes, previewRes, registryRes] = results;

        if (analysesRes.status === "fulfilled") {
          setAnalyses(analysesRes.value);
        } else {
          console.error("Fetch error (analyses):", analysesRes.reason);
        }

        if (previewRes.status === "fulfilled") {
          setDatasetPreview(previewRes.value);
        } else {
          console.error("Fetch error (dataset preview):", previewRes.reason);
        }

        if (registryRes.status === "fulfilled") {
          setFunctionRegistry(registryRes.value);
        } else {
          console.error("Fetch error (function registry):", registryRes.reason);
        }

        if (results[3].status === "fulfilled") {
          setSavedGraphs(results[3].value);
        } else {
          console.error("Fetch error (saved graphs):", results[3].reason);
        }
      };
      fetchData();
    }
  }, [datasetId]);

  // Function to add a new node
  const addNode = (newStep: PathStep) => {
    setPath((prev) => [...prev, newStep]);
  };

  // Function to delete a node by index
  const deleteNode = (index: number) => {
    setPath((prev) => prev.filter((_, i) => i !== index));
  };

  // Function to edit a node by index
  const editNode = (index: number, updates: Partial<PathStep>) => {
    setPath((prev) => prev.map((step, i) => (i === index ? { ...step, ...updates } : step)));
  };

  // Remove coerceFromInput as it's replaced by structured editors
  // (comment out or remove lines 110-123)

  if (!datasetId) {
    return (
      <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
        <h1 className="text-3xl font-bold mb-4">Graph Edit</h1>
        <p className="text-red-600">Error: No dataset_id provided in URL. Please load the page with ?dataset_id=your_id.</p>
      </main>
    );
  }

  const handleSave = async () => {
    try {
      const response = await save_graph(graphName, path);
      alert(`Saved graph: ${graphName} (ID: ${response.graph_id})`);
      
      // Poll after 10 seconds
      setTimeout(async () => {
        try {
          const updatedGraphs = await get_saved_graphs();
          setSavedGraphs(updatedGraphs);
          console.log("Refreshed saved graphs after 10s");
        } catch (err) {
          console.error("Failed to refresh saved graphs:", err);
        }
      }, 10000);
    } catch (error) {
      alert(`Save failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  // Function to run the current path
  const handleRunGraph = async () => {
    if (!datasetId || path.length === 0) {
      alert("Cannot run: Missing dataset_id or empty path");
      return;
    }
    try {
      const response = await runCompiler(datasetId, path);
      alert(`Analysis started: ${response.analysis_id}`);
    } catch (error) {
      alert(`Run failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  // Helper: render a compact dataset preview table
  const renderDatasetPreview = () => {
    if (!datasetPreview || !datasetPreview.head || datasetPreview.head.length === 0) {
      return <div className="text-sm text-gray-500">No preview available.</div>;
    }
    const columns = Object.keys(datasetPreview.head[0] || {});
    const rows = datasetPreview.head.slice(0, 5);
    return (
      <div className="overflow-auto border rounded-md">
        <table className="min-w-full text-xs">
          <thead className="bg-gray-100">
            <tr>
              {columns.map((col) => (
                <th key={col} className="px-2 py-1 text-left font-semibold text-gray-700 tracking-wide uppercase whitespace-nowrap">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row: any, idx: number) => (
              <tr key={idx} className="odd:bg-white even:bg-gray-50">
                {columns.map((col) => (
                  <td key={col} className="px-2 py-1 align-top text-gray-800">
                    <div className="max-h-16 overflow-auto break-words leading-snug">
                      {String(row[col] ?? "")}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const buildArgsTemplate = (fnName: string): Record<string, any> => {
    const meta = functionRegistry?.[fnName];
    if (!meta || !Array.isArray(meta.args)) return {};
    const out: Record<string, any> = {};
    for (const a of meta.args) {
      const inferred = inferEditor(a);
      out[a.name] = a.hasOwnProperty("default") && a.default !== undefined ? a.default :
                    inferred.type === "list" ? [] :
                    inferred.type === "dict" ? {} :
                    inferred.type === "number" ? 0 :
                    inferred.type === "boolean" ? false :
                    "";
    }
    return out;
  };

  return (
    <main className="min-h-screen bg-[#EAF5FF] p-4 sm:p-6 text-gray-800">
      <div className="flex gap-4">
        {/* Left sidebar styled like Figma */}
        <aside className="w-80 shrink-0 flex flex-col gap-4 bg-[#EAF5FF] border border-[#9CC7FF] rounded-2xl p-3">
          {/* Dataset Preview card with blue header */}
          <div className="border-2 border-[#9CC7FF] rounded-xl overflow-hidden shadow-sm">
            <div className="bg-[#5AA9FF] text-white text-sm font-semibold px-3 py-2 tracking-wide uppercase">Dataset Preview</div>
            <div className="bg-white p-3">
              <div className="text-xs text-gray-600 mb-2">
                {datasetPreview ? (
                  <div>
                    <div className="font-semibold text-gray-800">{datasetPreview.original_filename}</div>
                    <div className="text-gray-600">{datasetPreview.num_rows} rows</div>
                  </div>
                ) : (
                  <div>Loading...</div>
                )}
              </div>

              {/* Scrollable preview area with per-cell scroll */}
              <div className="h-56 overflow-auto border rounded-md">
                {renderDatasetPreview()}
              </div>
            </div>
          </div>

          {/* Sample Node Paths card with blue header */}
          <div className="border-2 border-[#9CC7FF] rounded-xl overflow-hidden shadow-sm">
            <div className="bg-[#5AA9FF] text-white text-sm font-semibold px-3 py-2 tracking-wide uppercase">Sample Node Paths</div>
            <div className="bg-white p-3">
              {savedGraphs.length === 0 ? (
                <div className="text-xs text-gray-500">No saved graphs yet.</div>
              ) : (
                <ul className="text-sm text-gray-800 space-y-1 max-h-40 overflow-auto">
                  {savedGraphs.map((g) => (
                    <li
                      key={g.id}
                      className="px-2 py-1 rounded cursor-pointer hover:bg-gray-100"
                      onDoubleClick={async () => {
                        try {
                          const data = await get_saved_graph(g.id);
                          setPath(data.path || []);
                          setGraphName(data.name);
                          alert(`Loaded graph: ${data.name}`);
                        } catch (error) {
                          alert(`Load failed: ${error instanceof Error ? error.message : String(error)}`);
                        }
                      }}
                    >
                      {g.name}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Run button anchored under sidebar sections */}
          <button
            onClick={handleRunGraph}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 shadow"
          >
            Run Analysis
          </button>
        </aside>

        {/* Builder area */}
        <section className="flex-1 bg-white rounded-xl shadow p-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-800">Workflow Builder</h1>
            <div className="flex items-center gap-2">
              <button onClick={handleSave} className="px-3 py-1.5 bg-gray-200 rounded hover:bg-gray-300 text-sm">Save</button>
              <button className="px-3 py-1.5 bg-gray-200 rounded hover:bg-gray-300 text-sm">Validate</button>
              <button onClick={handleRunGraph} className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Run</button>
              {/* Home button */}
              <Link href="/" aria-label="Home" className="inline-flex items-center justify-center w-9 h-9 rounded-md border border-gray-300 bg-white hover:bg-gray-100">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 10.5L12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-9.5Z" stroke="#1f2937" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </Link>
              <Link href="/insight-visualizer" className="px-3 py-1.5 bg-gray-200 rounded hover:bg-gray-300 text-sm">Visualizer</Link>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div className="flex flex-col gap-4">
              <div>
                <label className="block mb-2">
                  <span className="block text-gray-700 mb-1 font-medium">Graph Name</span>
                  <input
                    type="text"
                    value={graphName}
                    onChange={(e) => setGraphName(e.target.value)}
                    className="border w-full p-2 rounded"
                  />
                </label>

                <h2 className="text-lg font-semibold mb-3">Graph Path</h2>
                {path.map((step, index) => (
                  <div key={index} className="border p-4 mb-4 rounded-lg">
                    <label className="block mb-2">
                      Function:
                      <select
                        value={step.function}
                        onChange={(e) => {
                          const fn = e.target.value;
                          const template = buildArgsTemplate(fn);
                          editNode(index, { function: fn, args: template });
                        }}
                        className="border w-full p-2 rounded"
                      >
                        <option value="">Select Function</option>
                        {Object.keys(functionRegistry).map((fn) => (
                          <option key={fn} value={fn}>{fn}</option>
                        ))}
                      </select>
                    </label>

                    {/* Dynamic individual arg inputs */}
                    {step.function && functionRegistry?.[step.function]?.args?.length ? (
                      <div className="mb-3 text-sm text-gray-800">
                        {functionRegistry[step.function].args.map((a: any) => {
                          const inferred = inferEditor(a);
                          const current = step.args?.[a.name] ?? a.default ?? (inferred.type === "list" ? [] : inferred.type === "dict" ? {} : null);
                          return (
                            <label key={a.name} className="block mb-2">
                              <span className="block text-gray-700 mb-1 font-medium">
                                {a.name}{a.required ? " *" : ""}
                                {a.type ? <span className="ml-2 text-xs text-gray-500">({a.type})</span> : null}
                              </span>
                              <ArgEditor
                                inferred={inferred}
                                value={current}
                                onChange={(newValue) => {
                                  editNode(index, { args: { ...(step.args || {}), [a.name]: newValue } });
                                }}
                                parentFunction={step.function}  // Pass the current step's function
                                argName={a.name}                // Pass the arg name
                              />
                            </label>
                          );
                        })}

                        <button
                          type="button"
                          className="mt-1 px-2 py-1 border rounded text-gray-700 hover:bg-gray-100"
                          onClick={() => editNode(index, { args: buildArgsTemplate(step.function) })}
                        >
                          Reset Args to Template
                        </button>
                      </div>
                    ) : null}

                    <label className="block mb-2">
                      Input DF Name:
                      <input
                        type="text"
                        value={step.input_df_name}
                        onChange={(e) => editNode(index, { input_df_name: e.target.value })}
                        className="border w-full p-2 rounded"
                      />
                    </label>
                    <label className="block mb-2">
                      Output DF Name:
                      <input
                        type="text"
                        value={step.output_df_name}
                        onChange={(e) => editNode(index, { output_df_name: e.target.value })}
                        className="border w-full p-2 rounded"
                      />
                    </label>
                    <button
                      onClick={() => deleteNode(index)}
                      className="px-4 py-1 bg-red-600 text-white rounded hover:bg-red-700 mt-2"
                    >
                      Delete Node
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => addNode({ function: "", args: {}, input_df_name: "starting_df", output_df_name: "output_" + path.length })}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Add Node
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

// Add components
function ArgEditor({ inferred, value, onChange, parentFunction, argName }: ArgEditorProps) {
  switch (inferred.type) {
    case "text":
      return (
        <input
          type="text"
          className="border w-full p-2 rounded"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    case "number":
      return (
        <input
          type="number"
          className="border w-full p-2 rounded"
          value={value ?? ""}
          onChange={(e) => {
            const num = parseFloat(e.target.value);
            onChange(isNaN(num) ? null : num);
          }}
        />
      );
    case "boolean":
      return (
        <select
          className="border w-full p-2 rounded"
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value === "true")}
        >
          <option value="">Select</option>
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      );
    case "list":
      return <ListEditor value={value ?? []} inferred={inferred} onChange={onChange} parentFunction={parentFunction} argName={argName} />;
    case "dict":
      return <DictEditor value={value ?? {}} inferred={inferred} onChange={onChange} parentFunction={parentFunction} argName={argName} />;
    default:
      return (
        <textarea
          className="border w-full p-2 rounded"
          value={JSON.stringify(value) ?? ""}
          onChange={(e) => {
            try {
              onChange(JSON.parse(e.target.value));
            } catch {
              onChange(null);
            }
          }}
        />
      );
  }
}

function ListEditor({ value, inferred, onChange, parentFunction, argName }: ListEditorProps) {
  const [items, setItems] = useState<any[]>(value);

  useEffect(() => {
    setItems(value);
  }, [value]);

  const addItem = () => {
    let defaultItem;
    if (parentFunction === "binary_classification" && argName === "questions") {
      // Auto-populate for questions: list of dicts with specific keys
      defaultItem = {
        context_prompt: "",
        positive_label: "true",
        negative_label: "false",
        explanation_col: "binary_explanation",
        label_col: "binary_label",
        input_data: "call_text",
        include_explanation: "true",
      };
    } else {
      // Existing default logic
      defaultItem = inferred.itemType?.type === "number" ? 0 :
                    inferred.itemType?.type === "boolean" ? false :
                    inferred.itemType?.type === "list" ? [] :
                    inferred.itemType?.type === "dict" ? {} :
                    "";
    }
    setItems([...items, defaultItem]);
  };

  const updateItem = (idx: number, newVal: any) => {
    const newItems = [...items];
    newItems[idx] = newVal;
    setItems(newItems);
    onChange(newItems.filter(item => item !== "" && item !== null)); // Clean empties
  };

  const removeItem = (idx: number) => {
    const newItems = items.filter((_, i) => i !== idx);
    setItems(newItems);
    onChange(newItems);
  };

  return (
    <div className="border rounded p-2">
      {items.map((item, idx) => (
        <div key={idx} className="flex items-center mb-1">
          <ArgEditor
            inferred={inferred.itemType ?? { type: "text" }}
            value={item}
            onChange={(newVal) => updateItem(idx, newVal)}
            parentFunction={parentFunction}
            argName={argName}
          />
          <button type="button" onClick={() => removeItem(idx)} className="ml-2 text-red-600">x</button>
        </div>
      ))}
      <button type="button" onClick={addItem} className="mt-1 px-2 py-1 bg-green-200 rounded">+ Add Item</button>
    </div>
  );
}

function DictEditor({ value, inferred, onChange, parentFunction, argName }: DictEditorProps) {
  const [pairs, setPairs] = useState<{ key: string; value: any }[]>(
    Object.entries(value).map(([key, val]) => ({ key, value: val }))
  );

  useEffect(() => {
    setPairs(Object.entries(value).map(([key, val]) => ({ key, value: val })));
  }, [value]);

  const addPair = () => {
    setPairs([...pairs, { key: "", value: inferred.valueType?.type === "number" ? 0 :
                                   inferred.valueType?.type === "boolean" ? false :
                                   inferred.valueType?.type === "list" ? [] :
                                   inferred.valueType?.type === "dict" ? {} :
                                   "" }]);
  };

  const updatePair = (idx: number, field: "key" | "value", newVal: any) => {
    const newPairs = [...pairs];
    newPairs[idx] = { ...newPairs[idx], [field]: newVal };
    setPairs(newPairs);
    const newDict: Record<string, any> = {};
    newPairs.forEach(p => {
      if (p.key) newDict[p.key] = p.value;
    });
    onChange(newDict);
  };

  const removePair = (idx: number) => {
    const newPairs = pairs.filter((_, i) => i !== idx);
    setPairs(newPairs);
    const newDict: Record<string, any> = {};
    newPairs.forEach(p => {
      if (p.key) newDict[p.key] = p.value;
    });
    onChange(newDict);
  };

  return (
    <div className="border rounded p-2">
      {pairs.map((pair, idx) => (
        <div key={idx} className="flex items-center mb-1 gap-2">
          <input
            type="text"
            placeholder="Key"
            className="border p-1 rounded flex-1"
            value={pair.key}
            onChange={(e) => updatePair(idx, "key", e.target.value)}
          />
          <ArgEditor
            inferred={inferred.valueType ?? { type: "text" }}
            value={pair.value}
            onChange={(newVal) => updatePair(idx, "value", newVal)}
            parentFunction={parentFunction}
            argName={argName}
          />
          <button type="button" onClick={() => removePair(idx)} className="text-red-600">x</button>
        </div>
      ))}
      <button type="button" onClick={addPair} className="mt-1 px-2 py-1 bg-green-200 rounded">+ Add Pair</button>
    </div>
  );
}
