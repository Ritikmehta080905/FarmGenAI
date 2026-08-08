import React from 'react';
import { Settings, Sliders, Database, Save } from 'lucide-react';

export default function AIConfigPanel() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-800">AI Hyperparameters</h2>
          <p className="text-sm text-slate-500 mt-1">Configure LLMs, RAG generation, and LangGraph routing rules.</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold text-sm transition">
          <Save size={16} /> Save AI Configuration
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* LLM Routing */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6">
          <h3 className="font-bold text-slate-800 flex items-center gap-2 border-b pb-2"><Settings size={18} className="text-purple-600"/> LLM Routing Strategy</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Primary Orchestration Model</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option>gemini-1.5-pro-latest</option>
                <option>gemini-1.5-flash</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Fallback Extraction Model (Local)</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option>ollama/llama3:8b</option>
                <option>ollama/qwen2:7b</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1 flex justify-between">
                <span>Temperature (Creativity)</span>
                <span className="text-blue-600">0.2</span>
              </label>
              <input type="range" min="0" max="1" step="0.1" defaultValue="0.2" className="w-full" />
              <p className="text-xs text-slate-500 mt-1">Keep low (0.1 - 0.3) for strict business negotiations.</p>
            </div>
          </div>
        </div>

        {/* RAG Configuration */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6">
          <h3 className="font-bold text-slate-800 flex items-center gap-2 border-b pb-2"><Database size={18} className="text-emerald-600"/> Retrieval Augmented Generation (RAG)</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Embedding Model</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option>text-embedding-004 (Google)</option>
                <option>nomic-embed-text (Local)</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Top-K Retrieval</label>
                <input type="number" defaultValue="5" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Chunk Size</label>
                <input type="number" defaultValue="1024" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1 flex justify-between">
                <span>Similarity Threshold</span>
                <span className="text-blue-600">0.75</span>
              </label>
              <input type="range" min="0" max="1" step="0.05" defaultValue="0.75" className="w-full" />
            </div>
          </div>
        </div>

        {/* LangGraph Configuration */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6 lg:col-span-2">
          <h3 className="font-bold text-slate-800 flex items-center gap-2 border-b pb-2"><Sliders size={18} className="text-blue-600"/> LangGraph Engine Strategy</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Maximum Negotiation Iterations</label>
              <input type="number" defaultValue="15" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Force-terminate deal if agents loop without agreement.</p>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Agent Node Timeout (ms)</label>
              <input type="number" defaultValue="8000" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Maximum time allowed for a single agent to respond.</p>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Tool Execution Retries</label>
              <input type="number" defaultValue="3" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Number of retries for failing MCP Server tools.</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
