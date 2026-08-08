import React from 'react';
import { Link } from 'react-router-dom';
import { Sprout, Users, Shield, Cpu, BookOpen, ChevronLeft } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-2">
              <Sprout className="h-8 w-8 text-emerald-600" />
              <Link to="/" className="text-xl font-bold text-slate-900 tracking-tight hover:text-emerald-600 transition-colors">
                AgriNegotiator
              </Link>
            </div>
            <div className="flex space-x-4">
              <Link to="/" className="text-slate-600 hover:text-emerald-600 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center">
                <ChevronLeft className="w-4 h-4 mr-1" /> Back to Home
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-grow max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        
        <div className="text-center mb-16">
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
            About The Project
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            AgriNegotiator is a final-year engineering project aimed at revolutionizing agricultural supply chains through Autonomous Decentralized Multi-Agent Negotiation.
          </p>
        </div>

        <div className="space-y-12">
          
          {/* Section 1 */}
          <section className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-emerald-100 p-2 rounded-lg">
                <Cpu className="text-emerald-600 h-6 w-6" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">The Problem</h2>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Traditional agricultural supply chains are plagued by information asymmetry, middleman exploitation, and logistical inefficiencies. Farmers struggle to find fair prices, while buyers face difficulties securing reliable, high-quality produce. Organizing warehousing and transport requires significant manual overhead, often leading to spoilage and monetary loss.
            </p>
          </section>

          {/* Section 2 */}
          <section className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-emerald-100 p-2 rounded-lg">
                <Users className="text-emerald-600 h-6 w-6" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">The Solution</h2>
            </div>
            <p className="text-slate-600 leading-relaxed mb-4">
              AgriNegotiator leverages a <strong>Multi-Agent Reinforcement Learning (MARL)</strong> architecture using LangGraph. Instead of human-to-human haggling, stakeholders configure their requirements, bounds, and BATNA (Best Alternative to a Negotiated Agreement).
            </p>
            <ul className="list-disc list-inside text-slate-600 space-y-2 ml-4">
              <li><strong>AI Agents</strong> negotiate optimally on behalf of the users in microseconds.</li>
              <li><strong>Validator Agents</strong> ensure compliance with platform rules.</li>
              <li><strong>Dynamic Supply Chain Assembly</strong> automatically loops in Warehouse and Transport agents if the buyer cannot handle logistics.</li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-emerald-100 p-2 rounded-lg">
                <Shield className="text-emerald-600 h-6 w-6" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Architecture & Technology</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-2">Frontend</h3>
                <p className="text-sm text-slate-600">React.js, Vite, Tailwind CSS, shadcn/ui. Designed for real-time WebSocket telemetry and dynamic state visualization.</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-2">Backend</h3>
                <p className="text-sm text-slate-600">FastAPI, Python, PostgreSQL. Scalable async architecture handling the core business logic.</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-2">AI & Graph</h3>
                <p className="text-sm text-slate-600">LangGraph for orchestration. Redis Streams for Pub/Sub. ChromaDB for RAG matching based on distance and requirements.</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-2">Security</h3>
                <p className="text-sm text-slate-600">JWT-based RBAC, encrypted payload transmission, and distinct physical isolation of LLM inference nodes.</p>
              </div>
            </div>
          </section>

          {/* Section 4 */}
          <section className="bg-emerald-600 p-8 rounded-2xl shadow-md text-center text-white">
            <BookOpen className="h-12 w-12 mx-auto mb-4 text-emerald-200" />
            <h2 className="text-2xl font-bold mb-4">Academic Context</h2>
            <p className="text-emerald-50 mb-6 max-w-xl mx-auto">
              This platform represents a major final-year engineering capstone project exploring the intersection of Supply Chain Logistics, Game Theory, and Generative AI.
            </p>
            <Link to="/register" className="inline-block bg-white text-emerald-700 px-6 py-2 rounded-lg font-bold hover:bg-slate-100 transition-colors">
              Explore The Platform Demo
            </Link>
          </section>

        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 py-8 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-slate-400 text-sm">
            © {new Date().getFullYear()} AgriNegotiator Engineering Project.
          </p>
        </div>
      </footer>

    </div>
  );
}
