"use client";
import { useState } from "react";
import axios from "axios";


const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";


export default function UploadPage() {
const [file, setFile] = useState<File | null>(null);
const [result, setResult] = useState<string>("");
const [resume, setResume] = useState<any>(null);
const [loading, setLoading] = useState<boolean>(false);
const [error, setError] = useState<string>("");


const onUpload = async () => {
  if (!file) return;
  setLoading(true);
  setError("");
  try {
    const form = new FormData();
    form.append("file", file);
    const res = await axios.post(`${API}/parse`, form, { headers: { "Content-Type": "multipart/form-data" } });
    setResult(JSON.stringify(res.data, null, 2));
    setResume(res.data);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Upload failed");
  } finally {
    setLoading(false);
  }
};


return (
  <div className="p-6 space-y-4">
    <h1 className="text-2xl font-semibold">Upload Résumé</h1>
    <input type="file" onChange={(e)=> setFile(e.target.files?.[0] || null)} />
    <button 
      className="px-4 py-2 rounded bg-black text-white disabled:bg-gray-400" 
      onClick={onUpload}
      disabled={loading || !file}
    >
      {loading ? "Parsing..." : "Parse"}
    </button>
    {error && <div className="text-red-600 p-2 bg-red-50 rounded">{error}</div>}
    {resume && (
      <a
        className="inline-block mt-2 text-indigo-600 underline"
        href={`/dashboard/editor?rt=${encodeURIComponent(resume.resume_text || "")}`}
        target="_blank"
        rel="noreferrer"
      >
        Open in Editor →
      </a>
    )}
    <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">{result}</pre>
  </div>
);
}