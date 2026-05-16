import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  influencers: defineTable({
    name: v.string(),
    handle: v.string(),
    niche: v.string(),
  }).index("by_handle", ["handle"]),

  brandCollabs: defineTable({
    influencerId: v.id("influencers"),
    brandName: v.string(),
    dealType: v.string(),
    date: v.optional(v.string()),
    notes: v.optional(v.string()),
  }).index("by_influencer", ["influencerId"]),
});
