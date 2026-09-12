import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../lib/api';
import {
  Sparkles, Send, Bot, User, Trash2, BookOpen,
  Upload, CheckCircle, AlertCircle, FileText, X
} from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  is_ai_assisted?: boolean;
  timestamp: string;
}

interface PolicyDocument {
  policy_id: string;
  title: string;
  category: string;
  chunk_count: number;
  uploaded_at: string;
}

const SUGGESTED_PROMPTS = [
  "Analyze current attrition drivers across our departments",
  "How can we upskill software engineers for tech lead roles?",
  "What is our policy on remote work and flexible hours?",
  "Summarize our latest candidate pipeline and hiring metrics",
  "Generate an interview guide for a Senior Backend Developer"
];

export default function AICopilot() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiStatus, setAiStatus] = useState<{ is_configured: boolean; model: string } | null>(null);
  const [showPolicyDrawer, setShowPolicyDrawer] = useState(false);
  const [policies, setPolicies] = useState<PolicyDocument[]>([]);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCategory, setUploadCategory] = useState('Workplace');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    // Check AI status
    api.get('/ai/status')
      .then(res => setAiStatus(res.data))
      .catch(() => setAiStatus({ is_configured: false, model: 'demo-mode' }));

    // Fetch policy documents
    fetchPolicies();

    // Set welcome message
    setMessages([
      {
        role: 'assistant',
        content: `Hello! I am **NeuroHR Copilot**, powered by xAI Grok. I can help you analyze attrition risk factors, explore career pathways, review recruitment matching, and answer questions about your organization's internal HR policies. How can I assist you today?`,
        is_ai_assisted: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  }, []);

  const fetchPolicies = async () => {
    try {
      const res = await api.get('/ai/policies');
      setPolicies(res.data);
    } catch (e) {
      console.error("Failed to fetch policies", e);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputPrompt).trim();
    if (!text || loading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    setInputPrompt('');
    setLoading(true);

    try {
      const res = await api.post('/ai/copilot', {
        prompt: text
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: res.data.response,
        sources: res.data.sources || [],
        is_ai_assisted: res.data.is_ai_assisted,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || "Encountered an issue communicating with the AI service. Please try again.";
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ **Service Notice**: ${errorMsg}`,
          is_ai_assisted: false,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = async () => {
    try {
      await api.delete('/ai/copilot/history');
    } catch (e) {
      // ignore
    }
    setMessages([
      {
        role: 'assistant',
        content: `Conversation reset. How can I assist you with your workforce or policy needs?`,
        is_ai_assisted: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  const handleUploadPolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle.trim()) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', uploadTitle);
    formData.append('category', uploadCategory);

    try {
      await api.post('/ai/policies/upload', formData);
      setUploadSuccess(`Policy "${uploadTitle}" indexed successfully.`);
      setUploadTitle('');
      setUploadFile(null);
      fetchPolicies();
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDeletePolicy = async (policyId: string) => {
    if (!confirm("Are you sure you want to remove this policy document?")) return;
    try {
      await api.delete(`/ai/policies/${policyId}`);
      setPolicies(prev => prev.filter(p => p.policy_id !== policyId));
    } catch (err) {
      alert("Failed to delete policy");
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-gray-50 dark:bg-gray-950 overflow-hidden relative">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Copilot Bar */}
        <header className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">AI HR Copilot</h1>
                {aiStatus?.is_configured ? (
                  <span className="px-2 py-0.5 text-[11px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-full flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    xAI Grok ({aiStatus.model})
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[11px] font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded-full flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                    Demo Mode Active
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Tenant Isolated • Grounded Intelligence & HR Policy RAG
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowPolicyDrawer(true)}
              className="px-3.5 py-2 bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
            >
              <BookOpen className="w-4 h-4" />
              HR Policies ({policies.length})
            </button>
            <button
              onClick={handleClearChat}
              title="Clear conversation"
              className="p-2 text-gray-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Privacy & Scope Banner */}
          <div className="p-3.5 bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-2xl text-xs text-slate-600 dark:text-slate-400 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500" />
              <span>Grounded on Organization data. Employee PII is masked. Recommendations require managerial sign-off.</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">{user?.role}</span>
          </div>

          {messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={index}
                className={`flex gap-3.5 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-sm ${
                    isUser
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gradient-to-tr from-purple-600 to-indigo-600 text-white'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Bubble */}
                <div className={`space-y-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed ${
                      isUser
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/10 rounded-tr-none'
                        : 'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border border-gray-100 dark:border-gray-800 shadow-sm rounded-tl-none'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>

                    {/* Sources Citations */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800 text-xs text-indigo-600 dark:text-indigo-400 flex flex-wrap gap-2 items-center">
                        <span className="font-semibold text-gray-500 dark:text-gray-400">Sources:</span>
                        {msg.sources.map((src, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-indigo-50 dark:bg-indigo-950/40 rounded-md border border-indigo-200 dark:border-indigo-800 text-[11px]"
                          >
                            📄 {src}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className={`text-[10px] text-gray-400 flex items-center gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <span>{msg.timestamp}</span>
                    {!isUser && msg.is_ai_assisted && (
                      <span className="text-indigo-500 font-medium">• AI-Assisted Recommendation</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Pulsing loading state */}
          {loading && (
            <div className="flex gap-3 max-w-3xl mr-auto">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white flex items-center justify-center flex-shrink-0 text-xs shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm rounded-tl-none flex items-center gap-2 text-xs text-gray-500">
                <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                <span className="ml-1 text-gray-400">Grok is synthesizing answer...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts & Input Area */}
        <div className="p-4 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 flex-shrink-0 space-y-3">
          {/* Quick prompt chips */}
          {messages.length <= 2 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              {SUGGESTED_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(prompt)}
                  className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 hover:text-indigo-600 dark:hover:text-indigo-300 text-gray-600 dark:text-gray-300 rounded-xl text-xs font-medium whitespace-nowrap transition-all border border-gray-200 dark:border-gray-700 hover:border-indigo-300"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {/* Input Box */}
          <div className="relative flex items-center">
            <textarea
              rows={1}
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Copilot anything about attrition, skill gaps, candidate matches, or HR policies..."
              className="w-full pl-4 pr-24 py-3.5 bg-gray-50 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-2xl text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none transition-all"
            />
            <div className="absolute right-2 flex items-center gap-1.5">
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputPrompt.trim() || loading}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center gap-1.5"
              >
                <span>Send</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* HR Policy RAG Drawer */}
      {showPolicyDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="fixed inset-0 bg-black/40 backdrop-blur-xs" onClick={() => setShowPolicyDrawer(false)} />
          <div className="relative w-full max-w-md bg-white dark:bg-gray-900 h-full shadow-2xl border-l border-gray-100 dark:border-gray-800 flex flex-col z-10 p-6 space-y-6 overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-base font-bold text-gray-900 dark:text-white">HR Policy Knowledge Base</h3>
              </div>
              <button
                onClick={() => setShowPolicyDrawer(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-400">
              Upload company employee handbooks, leave guidelines, or remote work policies.
              The Copilot uses semantic retrieval (RAG) to ground policy answers strictly in these documents.
            </p>

            {/* Upload Form */}
            <form onSubmit={handleUploadPolicy} className="p-4 bg-gray-50 dark:bg-gray-800/60 rounded-2xl border border-gray-200 dark:border-gray-700 space-y-3">
              <h4 className="text-xs font-bold text-gray-700 dark:text-gray-200 uppercase tracking-wider">Index New Policy</h4>

              <div>
                <label className="text-xs text-gray-500 block mb-1">Document Title</label>
                <input
                  type="text"
                  placeholder="e.g. Remote Work Policy 2026"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-gray-500 block mb-1">Category</label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="Workplace">Workplace & Culture</option>
                  <option value="Leave & Benefits">Leave & Benefits</option>
                  <option value="Compensation">Compensation & Reviews</option>
                  <option value="Conduct">Code of Conduct</option>
                  <option value="General">General Handbook</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-500 block mb-1">Policy File (.txt or .pdf)</label>
                <input
                  type="file"
                  accept=".txt,.pdf"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-gray-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 dark:file:bg-indigo-900/40 dark:file:text-indigo-300 hover:file:bg-indigo-100"
                  required
                />
              </div>

              {uploadError && (
                <div className="p-2.5 bg-red-50 text-red-700 text-xs rounded-xl flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              {uploadSuccess && (
                <div className="p-2.5 bg-emerald-50 text-emerald-700 text-xs rounded-xl flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={uploading}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                <Upload className="w-3.5 h-3.5" />
                {uploading ? 'Processing & Indexing...' : 'Upload & Index Policy'}
              </button>
            </form>

            {/* Existing Documents List */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-gray-700 dark:text-gray-200 uppercase tracking-wider">Active Policy Documents ({policies.length})</h4>
              {policies.length === 0 ? (
                <p className="text-xs text-gray-400 italic">No policies uploaded yet for your organization.</p>
              ) : (
                <div className="space-y-2">
                  {policies.map(p => (
                    <div
                      key={p.policy_id}
                      className="p-3 bg-white dark:bg-gray-800/80 rounded-xl border border-gray-100 dark:border-gray-700 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <FileText className="w-4 h-4 text-indigo-500 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-gray-800 dark:text-gray-100 truncate">{p.title}</p>
                          <p className="text-[10px] text-gray-400">{p.category} • {p.chunk_count} passages</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeletePolicy(p.policy_id)}
                        className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        title="Delete policy"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
