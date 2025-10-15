"use client";
import { useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [resume, setResume] = useState<any>(null);
  const [jd, setJd] = useState("");
  const [align, setAlign] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  async function parse() {
    if (!file) return;
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/parse`, { method: "POST", body: form });
    const data = await res.json();
    setResume(data);
    setBusy(false);
  }

  async function doAlign() {
    if (!resume?.resume_text || !jd.trim()) return;
    setBusy(true);
    const res = await fetch(`${API}/align`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: resume.resume_text, jd_text: jd })
    });
    const data = await res.json();
    setAlign(data);
    setBusy(false);
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Step 2: Parse & Analyze</h1>
      <input type="file" accept=".pdf,.docx,.txt" onChange={e=>setFile(e.target.files?.[0]||null)} />
      <button className="px-4 py-2 rounded bg-black text-white" onClick={parse} disabled={!file || busy}>Parse</button>

      {resume && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-3 rounded">
            <h2 className="font-medium mb-2">Parsed Structure</h2>
            <pre className="text-xs overflow-auto max-h-80">{JSON.stringify(resume.structure_json, null, 2)}</pre>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <h2 className="font-medium mb-2">Resume Text (for scoring)</h2>
            <pre className="text-xs overflow-auto max-h-80">{resume.resume_text}</pre>
          </div>
        </div>
      )}

      <textarea className="w-full h-40 p-2 border rounded" placeholder="Paste Job Description here" value={jd} onChange={e=>setJd(e.target.value)} />
      <button className="px-4 py-2 rounded bg-indigo-600 text-white" onClick={doAlign} disabled={!resume || !jd || busy}>Analyze JD vs Resume</button>

      {align && (
        <div className="bg-white border rounded p-3">
          <div className="text-lg">Alignment Score: <span className="font-semibold">{align.score}</span></div>
          <div className="mt-2 text-sm text-gray-700">JD Keywords: {align.jd_keywords.join(", ")}</div>
          <div className="mt-2 text-sm text-red-600">Missing: {align.missing_keywords.join(", ") || "(none)"}</div>
        </div>
      )}
    </div>
  );
}
