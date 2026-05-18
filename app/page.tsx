"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useState, useMemo } from "react";

const CATEGORIES = ["Beauty", "Fashion", "Tech", "Food", "Fitness", "Travel", "Finance", "Education", "Entertainment", "Lifestyle"];

type Tab = "creator" | "brand";
type SortOption = "relevance" | "name" | "collabs";

export default function Home() {
  const influencers = useQuery(api.influencers.list);
  const [tab, setTab] = useState<Tab>("creator");
  const [query, setQuery] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [sort, setSort] = useState<SortOption>("relevance");

  const results = useMemo(() => {
    if (!influencers) return [];
    let filtered = influencers;

    if (query.trim()) {
      const q = query.toLowerCase();
      if (tab === "creator") {
        filtered = filtered.filter(
          (inf) => inf.name.toLowerCase().includes(q) || inf.handle.toLowerCase().includes(q)
        );
      } else {
        filtered = filtered.filter((inf) =>
          inf.brandCollabs.some((c) => c.brandName.toLowerCase().includes(q))
        );
      }
    }

    if (selectedCategories.length > 0) {
      filtered = filtered.filter((inf) => selectedCategories.includes(inf.niche));
    }

    if (sort === "name") {
      filtered = [...filtered].sort((a, b) => a.name.localeCompare(b.name));
    } else if (sort === "collabs") {
      filtered = [...filtered].sort((a, b) => b.brandCollabs.length - a.brandCollabs.length);
    }

    return filtered;
  }, [influencers, query, tab, selectedCategories, sort]);

  const categoryCounts = useMemo(() => {
    if (!influencers) return {} as Record<string, number>;
    return influencers.reduce((acc, inf) => {
      acc[inf.niche] = (acc[inf.niche] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [influencers]);

  const toggleCategory = (cat: string) => {
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-8 py-5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Creatorpedia</h1>
            <p className="text-sm text-gray-400 mt-0.5">Influencer–brand collaboration database</p>
          </div>
          <a
            href="/influencers/new"
            className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Add Influencer
          </a>
        </div>
      </header>

      {/* Search panel */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-8 py-6">
          {/* Tabs */}
          <div className="flex gap-8 mb-5 border-b border-gray-200">
            <button
              onClick={() => { setTab("creator"); setQuery(""); }}
              className={`pb-3 text-sm font-semibold tracking-wide uppercase transition-colors ${
                tab === "creator"
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              Search by Creator
            </button>
            <button
              onClick={() => { setTab("brand"); setQuery(""); }}
              className={`pb-3 text-sm font-semibold tracking-wide uppercase transition-colors ${
                tab === "brand"
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              Search by Brand
            </button>
          </div>

          {/* Search input */}
          <div className="flex gap-3">
            <div className="flex-1 flex items-center gap-3 bg-white border border-gray-300 rounded-xl px-4 py-3 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100">
              <svg className="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={tab === "creator" ? "Search by creator name or @handle..." : "Search by brand name..."}
                className="flex-1 outline-none text-gray-800 placeholder-gray-400 text-sm"
              />
              {query && (
                <button onClick={() => setQuery("")} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
              )}
            </div>
            <button className="bg-blue-600 text-white font-semibold px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors text-sm">
              Search
            </button>
          </div>

          {/* Quick filter chips */}
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            <span className="text-sm text-gray-400">Try:</span>
            {["beauty", "fashion", "tech", "food", "fitness"].map((cat) => (
              <button
                key={cat}
                onClick={() => setQuery(cat)}
                className="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-500 hover:border-blue-300 hover:text-blue-600 transition-colors capitalize"
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="max-w-7xl mx-auto px-8 py-8 flex gap-8">
        {/* Sidebar filters */}
        <aside className="w-56 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-semibold text-gray-700">Filters</span>
              {selectedCategories.length > 0 && (
                <button
                  onClick={() => setSelectedCategories([])}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Clear All
                </button>
              )}
            </div>

            <p className="text-xs text-gray-400 uppercase tracking-wider mb-3">Category</p>
            <div className="space-y-2">
              {CATEGORIES.map((cat) => (
                <label key={cat} className="flex items-center justify-between cursor-pointer group">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selectedCategories.includes(cat)}
                      onChange={() => toggleCategory(cat)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600 group-hover:text-gray-900">{cat}</span>
                  </div>
                  <span className="text-xs text-gray-400">{categoryCounts[cat] || 0}</span>
                </label>
              ))}
            </div>
          </div>
        </aside>

        {/* Results */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-5">
            <p className="text-sm text-gray-500">
              {influencers === undefined
                ? "Loading..."
                : `Found ${results.length} influencer${results.length !== 1 ? "s" : ""}`}
            </p>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortOption)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-100"
            >
              <option value="relevance">Sort by: Relevance</option>
              <option value="name">Sort by: Name</option>
              <option value="collabs">Sort by: Most Collabs</option>
            </select>
          </div>

          {influencers === undefined ? (
            <div className="text-center py-24 text-gray-400">
              <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p>Loading influencers...</p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-24 text-gray-400">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <p className="text-lg">No influencers found.</p>
              <p className="text-sm mt-1">Try adjusting your filters.</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {results.map((inf) => (
                <div key={inf._id} className="bg-white rounded-xl border border-gray-200 p-6 hover:border-gray-300 hover:shadow-sm transition-all">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-gray-900">{inf.name}</h2>
                      <p className="text-blue-600 text-sm mt-0.5">@{inf.handle}</p>
                      <span className="inline-block mt-2 text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
                        {inf.niche}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400 bg-gray-50 border border-gray-100 px-2.5 py-1 rounded-full">
                      {inf.brandCollabs.length} collab{inf.brandCollabs.length !== 1 ? "s" : ""}
                    </span>
                  </div>

                  {inf.brandCollabs.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {inf.brandCollabs.map((collab) => (
                        <span
                          key={collab._id}
                          className="text-xs bg-blue-50 text-blue-700 border border-blue-100 px-3 py-1 rounded-full"
                        >
                          {collab.brandName}
                          {collab.dealType && (
                            <span className="ml-1 text-blue-400">· {collab.dealType}</span>
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
