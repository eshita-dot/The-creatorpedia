"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";

export default function Home() {
  const influencers = useQuery(api.influencers.list);

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-8 py-6">
        <h1 className="text-3xl font-bold text-gray-900">Creatorpedia</h1>
        <p className="text-gray-500 mt-1">Influencer–brand collaboration database</p>
      </header>

      <div className="max-w-6xl mx-auto px-8 py-10">
        <div className="flex items-center justify-between mb-6">
          <p className="text-sm text-gray-500">
            {influencers === undefined ? "Loading..." : `${influencers.length} influencers`}
          </p>
          <a
            href="/influencers/new"
            className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Add Influencer
          </a>
        </div>

        {influencers === undefined ? (
          <div className="text-center py-24 text-gray-400">
            <p className="text-lg">Loading...</p>
          </div>
        ) : influencers.length === 0 ? (
          <div className="text-center py-24 text-gray-400">
            <p className="text-lg">No influencers yet.</p>
            <p className="text-sm mt-1">Add one to get started.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {influencers.map((inf) => (
              <div key={inf._id} className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">{inf.name}</h2>
                    <p className="text-blue-600 text-sm">@{inf.handle}</p>
                    <span className="inline-block mt-2 text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      {inf.niche}
                    </span>
                  </div>
                  <span className="text-sm text-gray-400">{inf.brandCollabs.length} collabs</span>
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
    </main>
  );
}
