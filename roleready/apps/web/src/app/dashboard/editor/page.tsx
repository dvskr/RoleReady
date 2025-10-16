"use client";
import { useEffect, useMemo, useState, useCallback, useRef } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Highlight } from "@/packages/extensions/highlight";
import { CommentAnchor } from "@/packages/extensions/commentAnchor";
import { getResume, updateResume } from "@/lib/resumes";
import { supabase } from "@/lib/supabaseClient";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Debounce hook
function useDebounce(fn: (...args: any[]) => void, ms: number) {
  const t = useRef<any>();
  return useCallback((...args: any[]) => {
    clearTimeout(t.current);
    t.current = setTimeout(() => fn(...args), ms);
  }, [fn, ms]);
}

export default function EditorPage() {
  const q = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
  const prefill = q?.get("rt") || "";
  const id = q?.get("id") || "";
  const jdPrefill = q?.get("jd") || "";
  const [resumeText, setResumeText] = useState(prefill);
  const [jdText, setJdText] = useState(jdPrefill);
  const [align, setAlign] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [versions, setVersions] = useState<any[]>([]);
  const [theme, setTheme] = useState<'modern' | 'classic'>('modern');
  const [comments, setComments] = useState<any[]>([]);
  const [showComments, setShowComments] = useState(false);

  const editor = useEditor({
    extensions: [StarterKit, Highlight, CommentAnchor],
    content: "Paste your resume text here…",
    immediatelyRender: false,
  });

  useEffect(() => {
    if (editor && resumeText) editor.commands.setContent(resumeText.replace(/\n/g, "<br/>"));
  }, [editor, resumeText]);

  // Load resume by ID
  useEffect(() => {
    if (!id || !editor) return;
    (async () => {
      try {
        const data = await getResume(id);
        if (data) {
          editor.commands.setContent((data.content || '').replace(/\n/g, '<br/>'));
        }
      } catch (error) {
        console.error('Failed to load resume:', error);
      }
    })();
  }, [id, editor]);

  // Load versions when ID changes
  useEffect(() => {
    if (id) loadVersions();
  }, [id]);

  // Load comments when ID changes
  useEffect(() => {
    if (id) loadComments();
  }, [id]);

  // Realtime comments subscription
  useEffect(() => {
    if (!id) return;
    
    const channel = supabase.channel(`resume:${id}`);
    
    channel.on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'comments',
        filter: `resume_id=eq.${id}`
      },
      (payload) => {
        console.log('Comment change:', payload);
        loadComments();
      }
    );
    
    channel.subscribe();
    
    return () => {
      supabase.removeChannel(channel);
    };
  }, [id]);

  // Editor change listener for autosave
  useEffect(() => {
    if (!editor) return;
    const un = editor.on('update', onEditorChange);
    return () => { 
      if (typeof un === 'function') {
        un();
      } else if (un && typeof un.unsubscribe === 'function') {
        un.unsubscribe();
      }
    };
  }, [editor, onEditorChange]);

  // Debounced autosave function
  const debouncedSave = useDebounce(async (text: string) => {
    if (!id) return;
    setSaving('saving');
    try {
      await updateResume(id, text);
      setSaving('saved');
      setTimeout(() => setSaving('idle'), 1200);
    } catch (error) {
      console.error('Autosave failed:', error);
      setSaving('idle');
    }
  }, 5000);

  // Editor change handler
  const onEditorChange = useCallback(() => {
    const text = editor?.state.doc.textBetween(0, editor.state.doc.content.size, "\n") || '';
    debouncedSave(text);
  }, [editor, debouncedSave]);

  // Save function (manual save)
  async function save() {
    if (!id || !editor) return;
    try {
      const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
      await updateResume(id, text);
      setSaving('saved');
      setTimeout(() => setSaving('idle'), 1200);
    } catch (error) {
      console.error('Failed to save:', error);
      alert('Failed to save');
    }
  }

  // Load versions function
  async function loadVersions() {
    if (!id) return;
    try {
      const { data } = await supabase
        .from('resume_versions')
        .select('*')
        .eq('resume_id', id)
        .order('created_at', { ascending: false });
      setVersions(data || []);
    } catch (error) {
      console.warn('Failed to load versions:', error);
    }
  }

  // Load comments function
  async function loadComments() {
    if (!id) return;
    try {
      const { data } = await supabase
        .from('comments')
        .select('*')
        .eq('resume_id', id)
        .eq('resolved', false)
        .order('created_at', { ascending: true });
      setComments(data || []);
    } catch (error) {
      console.warn('Failed to load comments:', error);
    }
  }

  // Add comment function
  async function addComment() {
    if (!editor || !id) return;
    
    const { from, to } = editor.state.selection;
    if (from === to) {
      alert('Select text to comment on');
      return;
    }
    
    const text = prompt('Enter your comment:');
    if (!text) return;
    
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        alert('Please sign in to add comments');
        return;
      }
      
      const { data, error } = await supabase
        .from('comments')
        .insert({
          resume_id: id,
          user_id: user.id,
          anchor_from: from,
          anchor_to: to,
          text: text
        })
        .select()
        .single();
      
      if (error) throw error;
      
      // Add comment anchor to editor
      const commentId = `c-${data.id}`;
      editor.chain().setMark('commentAnchor', { id: commentId }).run();
      
      await loadComments();
      alert('Comment added successfully!');
    } catch (error) {
      console.error('Failed to add comment:', error);
      alert('Failed to add comment');
    }
  }

  // Resolve comment function
  async function resolveComment(commentId: string) {
    try {
      await supabase
        .from('comments')
        .update({ resolved: true })
        .eq('id', commentId);
      
      await loadComments();
    } catch (error) {
      console.error('Failed to resolve comment:', error);
    }
  }

  // Manual snapshot function
  async function saveSnapshot() {
    if (!id) return;
    try {
      await supabase.rpc('manual_snapshot', { r_id: id });
      await loadVersions();
      alert('Snapshot saved!');
    } catch (error) {
      console.error('Failed to save snapshot:', error);
      alert('Failed to save snapshot');
    }
  }

  // Restore version function
  async function restoreVersion(vid: string) {
    const v = versions.find(x => x.id === vid);
    if (!v || !editor) return;
    try {
      await updateResume(id, v.content);
      editor.commands.setContent(v.content.replace(/\n/g, '<br/>'));
      await loadVersions();
      setSaving('saved');
      setTimeout(() => setSaving('idle'), 1200);
    } catch (error) {
      console.error('Failed to restore version:', error);
      alert('Failed to restore version');
    }
  }

  // Export DOCX function
  async function exportDocx() {
    if (!editor) return;
    try {
      const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
      const res = await fetch(`${API}/export/docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'RoleReady_Resume', content: text })
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'RoleReady_Resume.docx';
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export DOCX:', error);
      alert('Failed to export DOCX');
    }
  }

  // Export DOCX with Template function
  async function exportDocxTemplate() {
    if (!editor) return;
    try {
      const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
      const res = await fetch(`${API}/export/docx-template`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          template: 'classic.docx',
          title: 'RoleReady_Resume', 
          content: text 
        })
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'RoleReady_Resume_Template.docx';
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export DOCX Template:', error);
      alert('Failed to export DOCX Template');
    }
  }

  // Export PDF function
  async function exportPDF() {
    if (!editor) return;
    try {
      const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
      
      // Simple PDF generation using browser print with theme
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head>
              <title>Resume Export - ${theme} theme</title>
              <link rel="stylesheet" href="/styles/themes/${theme}.css" media="print">
              <style>
                body { margin: 0; padding: 0; }
                .resume { font-family: ${theme === 'classic' ? 'Times New Roman, serif' : 'Segoe UI, sans-serif'}; }
                @media print {
                  body { margin: 0; padding: 0; }
                  .resume { margin: 0; padding: ${theme === 'classic' ? '1in' : '0.5in'}; }
                }
              </style>
            </head>
            <body>
              <div class="resume theme-${theme}">
                <div class="content">${text}</div>
              </div>
            </body>
          </html>
        `);
        printWindow.document.close();
        printWindow.print();
      }
    } catch (error) {
      console.error('Failed to export PDF:', error);
      alert('Failed to export PDF');
    }
  }

  // Keyword highlighting effect
  useEffect(() => {
    if (!editor || !align?.jd_keywords) return;
    
    // Clear existing highlights
    editor.commands.unsetHighlight();
    
    const content = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
    
    // Highlight each JD keyword
    align.jd_keywords.forEach((kw: string) => {
      const re = new RegExp(`\\b${kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, "gi");
      let match;
      while ((match = re.exec(content)) !== null) {
        const from = match.index;
        const to = from + kw.length;
        editor.commands.setTextSelection({ from, to });
        editor.commands.setHighlight({ color: "#bbf7d0" });
      }
    });
  }, [editor, align]);

  // Extract skills from resume text (simple heuristic)
  function extractSkills(text: string): string[] {
    const skills: string[] = [];
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);
    
    // Look for skills sections
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].toLowerCase();
      if (line.includes('skills') || line.includes('technical') || line.includes('technologies') || 
          line.includes('expertise') || line.includes('proficiencies') || line.includes('core strengths')) {
        // Take the next few lines as skills
        for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
          const skillLine = lines[j];
          if (skillLine.includes(':') || skillLine.includes(',') || skillLine.includes('•')) {
            const extracted = skillLine.split(/[:,•]/).map(s => s.trim()).filter(s => s.length > 0);
            skills.push(...extracted);
          }
        }
        break;
      }
    }
    
    // Also extract common tech terms from the entire text
    const techTerms = text.match(/\b(?:Python|Java|JavaScript|React|Node\.?js|AWS|Azure|Docker|Kubernetes|SQL|MongoDB|PostgreSQL|Git|Linux|Windows|macOS|HTML|CSS|TypeScript|Angular|Vue|Spring|Django|Flask|Express|REST|API|JSON|XML|GraphQL|Redis|Elasticsearch|Kafka|Spark|Hadoop|TensorFlow|PyTorch|Pandas|NumPy|Scikit-learn|Machine Learning|AI|Data Science|DevOps|CI\/CD|Jenkins|GitHub|GitLab|Jira|Confluence|Agile|Scrum|Kanban)\b/gi);
    if (techTerms) {
      skills.push(...techTerms.map(t => t.trim()));
    }
    
    return [...new Set(skills)].slice(0, 20); // Remove duplicates and limit
  }

  async function analyze() {
    if (!editor || !jdText.trim()) return;
    setBusy(true);
    const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
    const res = await fetch(`${API}/align`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: text, jd_text: jdText, mode: "semantic" })
    });
    const data = await res.json();
    setAlign(data);
    setBusy(false);
  }

  // Create targeted resume function
  async function createTargetedResume() {
    if (!editor || !jdText.trim()) return;
    
    const jobTitle = prompt("Enter job title for this targeted resume:");
    if (!jobTitle) return;
    
    setBusy(true);
    try {
      const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        alert('Please log in to create targeted resumes');
        return;
      }

      const res = await fetch(`${API}/target/target`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ 
          resume_text: text, 
          jd_text: jdText,
          base_resume_id: id,
          job_title: jobTitle,
          title: `Targeted for ${jobTitle} - ${new Date().toLocaleDateString()}`
        })
      });
      
      if (!res.ok) {
        throw new Error('Failed to create targeted resume');
      }
      
      const data = await res.json();
      
      // Redirect to the new targeted resume
      window.location.href = `/dashboard/editor?id=${data.resume_id}`;
      
    } catch (error) {
      console.error('Failed to create targeted resume:', error);
      alert('Failed to create targeted resume. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  // Analyze JD match function
  async function analyzeMatch() {
    if (!editor || !jdText.trim()) return;
    
    setBusy(true);
    try {
      const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        alert('Please log in to analyze resume match');
        return;
      }

      const res = await fetch(`${API}/target/analyze-match`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ 
          resume_text: text, 
          jd_text: jdText
        })
      });
      
      if (!res.ok) {
        throw new Error('Failed to analyze match');
      }
      
      const analysis = await res.json();
      
      // Show analysis in an alert (in production, this would be a modal)
      const message = `Match Score: ${analysis.match_score}/100\n\n` +
        `Strengths:\n${analysis.strengths?.join('\n• ') || 'None listed'}\n\n` +
        `Weaknesses:\n${analysis.weaknesses?.join('\n• ') || 'None listed'}\n\n` +
        `Missing Keywords:\n${analysis.missing_keywords?.join(', ') || 'None'}\n\n` +
        `Recommendations:\n${analysis.recommendations?.join('\n• ') || 'None listed'}`;
      
      alert(message);
      
    } catch (error) {
      console.error('Failed to analyze match:', error);
      alert('Failed to analyze resume match. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  const heat = useMemo(() => {
    if (!align?.per_jd) return [] as { bullet: string; score: number }[];
    const map = new Map<string, number>();
    for (const row of align.per_jd) {
      const b = row.best_bullet as string;
      map.set(b, Math.max(map.get(b) ?? 0, row.similarity));
    }
    return Array.from(map.entries()).map(([bullet, sim]) => ({ bullet, score: Math.round(sim * 100) }));
  }, [align]);

  return (
    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <h1 className="text-xl font-semibold mb-2">Editor (semantic)</h1>
        <textarea className="w-full h-32 border p-2 rounded mb-2" placeholder="Paste Job Description here" value={jdText} onChange={e=>setJdText(e.target.value)} />
        <div className="flex gap-2 mb-3 flex-wrap">
          <button onClick={()=>setResumeText(prev=>prev)} className="px-3 py-2 bg-gray-200 rounded">Load from Upload page text</button>
          <button onClick={analyze} disabled={busy} className="px-3 py-2 bg-indigo-600 text-white rounded">Analyze</button>
          <button onClick={analyzeMatch} disabled={busy} className="px-3 py-2 bg-purple-600 text-white rounded">📊 Match Analysis</button>
          <button onClick={createTargetedResume} disabled={busy} className="px-3 py-2 bg-amber-600 text-white rounded">🎯 Tailor for JD</button>
          <button onClick={save} className="px-3 py-2 bg-green-600 text-white rounded">💾 Save</button>
          <button onClick={saveSnapshot} className="px-3 py-2 bg-blue-600 text-white rounded">📸 Snapshot</button>
          <button onClick={addComment} className="px-3 py-2 bg-yellow-600 text-white rounded">💬 Add Comment</button>
          <button onClick={() => setShowComments(!showComments)} className="px-3 py-2 bg-orange-600 text-white rounded">
            💬 Comments ({comments.length})
          </button>
        </div>
        
        {/* Theme Selection */}
        <div className="flex gap-2 mb-3 items-center">
          <span className="text-sm font-medium">Theme:</span>
          <select 
            value={theme} 
            onChange={(e) => setTheme(e.target.value as 'modern' | 'classic')}
            className="px-2 py-1 border rounded text-sm"
          >
            <option value="modern">Modern</option>
            <option value="classic">Classic</option>
          </select>
        </div>
        
        {/* Export Buttons */}
        <div className="flex gap-2 mb-3 flex-wrap">
          <button onClick={exportDocx} className="px-3 py-2 bg-black text-white rounded">📄 DOCX Basic</button>
          <button onClick={exportDocxTemplate} className="px-3 py-2 bg-purple-600 text-white rounded">📄 DOCX Template</button>
          <button onClick={exportPDF} className="px-3 py-2 bg-emerald-600 text-white rounded">📋 PDF ({theme})</button>
        </div>
        <div className="text-xs text-gray-500 mb-2">
          {saving === 'saving' ? 'Saving…' : saving === 'saved' ? 'Saved ✓' : ''}
        </div>
        <div className="border rounded p-2 min-h-[300px] bg-white">
          <div id="editor-printable" className="prose max-w-none">
            <EditorContent editor={editor} />
          </div>
        </div>
      </div>

      <div>
        <h2 className="font-medium mb-2">Heatmap (by best JD match)</h2>
        <div className="space-y-2">
          {heat.map((h, i) => (
            <div key={i} className="border rounded p-2">
              <div className="text-sm mb-1">{h.bullet}</div>
              <div className="h-2 bg-gray-200 rounded">
                <div className="h-2 rounded" style={{ width: `${h.score}%`, background: `linear-gradient(90deg, #ddd, #4f46e5)` }} />
              </div>
              <div className="text-xs text-gray-600 mt-1">Score: {h.score}</div>
            </div>
          ))}
          {!heat.length && <div className="text-sm text-gray-500">Run Analyze to see coverage.</div>}
        </div>

        {align && (
          <div className="mt-4 text-sm">
            <div className="mb-2">Overall Score: <b>{align.score}</b> (mode: {align.mode})</div>
            <div className="mb-2">Missing keywords: <span className="text-red-600">{align.missing_keywords.join(", ") || "(none)"}</span></div>
            <details className="mt-2">
              <summary className="cursor-pointer">Per‑JD best matches</summary>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                {align.per_jd.map((row: any, idx: number) => (
                  <li key={idx}><b>JD:</b> {row.jd_line} <br /> <b>Best:</b> {row.best_bullet} <i>({(row.similarity*100).toFixed(0)}%)</i></li>
                ))}
              </ul>
            </details>
          </div>
        )}

        {/* Rewrite Button */}
        <button
          className="mt-3 px-3 py-2 bg-amber-500 text-white rounded hover:bg-amber-600 disabled:opacity-50"
          disabled={!align || busy}
          onClick={async () => {
            if (!editor || !align?.jd_keywords) return;
            setBusy(true);
            try {
              const text = editor.state.doc.textBetween(0, editor.state.doc.content.size, "\n");
              const skills = extractSkills(text);
              const res = await fetch(`${API}/rewrite`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  section: "experience",
                  text: text,
                  jd_keywords: align.jd_keywords || [],
                  resume_skills: skills
                })
              });
              const data = await res.json();
              editor.commands.setContent(data.rewritten.replace(/\n/g, "<br/>").trim());
            } catch (error) {
              console.error("Rewrite failed:", error);
            } finally {
              setBusy(false);
            }
          }}
        >
          ✍️ Rewrite Section (Smart)
        </button>

        {/* Save Button */}
        {id && (
          <button
            className="mt-2 px-3 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50"
            onClick={save}
          >
            💾 Save
          </button>
        )}

        {/* Comments Panel */}
        {showComments && (
          <div className="mt-4">
            <h3 className="font-medium mb-2">Comments ({comments.length})</h3>
            <aside className="border rounded p-2 max-h-96 overflow-auto">
              <div className="space-y-2">
                {comments.length === 0 ? (
                  <div className="text-sm text-gray-500">No comments yet</div>
                ) : (
                  comments.map(comment => (
                    <div key={comment.id} className="p-2 border rounded bg-gray-50">
                      <div className="text-xs text-gray-600 mb-1">
                        {new Date(comment.created_at).toLocaleString()}
                      </div>
                      <div className="text-sm mb-2">{comment.text}</div>
                      <button
                        onClick={() => resolveComment(comment.id)}
                        className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                      >
                        ✓ Resolve
                      </button>
                    </div>
                  ))
                )}
              </div>
            </aside>
          </div>
        )}

        {/* Version History */}
        {id && versions.length > 0 && (
          <div className="mt-4">
            <h3 className="font-medium mb-2">Version History</h3>
            <aside className="border rounded p-2 max-h-96 overflow-auto">
              <div className="space-y-1">
                {versions.map(v => (
                  <div key={v.id} className="flex items-center justify-between text-xs p-2 border rounded">
                    <span>{new Date(v.created_at).toLocaleString()}</span>
                    <button 
                      className="underline text-blue-600 hover:text-blue-800" 
                      onClick={() => restoreVersion(v.id)}
                    >
                      Restore
                    </button>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        )}
      </div>
    </div>
  );
}

