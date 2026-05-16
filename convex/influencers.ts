import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {},
  handler: async (ctx) => {
    const influencers = await ctx.db.query("influencers").order("desc").take(100);
    return await Promise.all(
      influencers.map(async (inf) => {
        const brandCollabs = await ctx.db
          .query("brandCollabs")
          .withIndex("by_influencer", (q) => q.eq("influencerId", inf._id))
          .take(50);
        return { ...inf, brandCollabs };
      })
    );
  },
});

export const create = mutation({
  args: {
    name: v.string(),
    handle: v.string(),
    niche: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("influencers")
      .withIndex("by_handle", (q) => q.eq("handle", args.handle))
      .unique();
    if (existing) return existing._id;
    return await ctx.db.insert("influencers", {
      name: args.name,
      handle: args.handle,
      niche: args.niche,
    });
  },
});

export const addBrandCollab = mutation({
  args: {
    influencerId: v.id("influencers"),
    brandName: v.string(),
    dealType: v.string(),
    date: v.optional(v.string()),
    notes: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("brandCollabs", args);
  },
});
