import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";

const http = httpRouter();

http.route({
  path: "/add-influencer",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    const body = await req.json();
    const influencerId = await ctx.runMutation(api.influencers.create, {
      name: body.name,
      handle: body.handle,
      niche: body.niche ?? "Lifestyle",
    });

    if (Array.isArray(body.brandCollabs)) {
      for (const collab of body.brandCollabs) {
        await ctx.runMutation(api.influencers.addBrandCollab, {
          influencerId,
          brandName: collab.brandName,
          dealType: collab.dealType,
          date: collab.date,
          notes: collab.notes,
        });
      }
    }

    return new Response(JSON.stringify({ success: true, influencerId }), {
      headers: { "Content-Type": "application/json" },
    });
  }),
});

export default http;
