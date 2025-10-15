Files used: [`builds/csv/center.csv:1`](builds/csv/center.csv:1), [`builds/csv/pf.csv:1`](builds/csv/pf.csv:1), [`builds/csv/pg.csv:1`](builds/csv/pg.csv:1), [`builds/csv/sf.csv:1`](builds/csv/sf.csv:1), [`builds/csv/sg.csv:1`](builds/csv/sg.csv:1)

BRANDBOARD — 30 concise, actionable use-cases (grouped). Each entry: one-line description; 3 implementation steps; required CSV fields; example UX; tech stack; monetization; complexity; 1 risk.

PLAYER-FACING PRODUCTS
1) Build Generator (random + constraints)
- What: Generate a playable build by role, height, playstyle.
- Steps: load CSVs → filter by Position/Height/Playstyle terms → format build card + upgrade checklist.
- Fields: Build Name, Position, Height, all attribute columns.
- UX: "Generate" button → shows build card + recommended badges.
- Stack: React, Flask, SQLite, CSV import script.
- Monetization: ad-supported + premium save/export.
- Complexity: quick win.
- Risk: misleading recommendations if CSV ranges ambiguous.

2) Build Optimizer (stat-budget allocator)
- What: Suggest attribute spread to reach target archetype under point cap.
- Steps: parse target archetype stats → compute nearest feasible attribute vector → display upgrade steps.
- Fields: Build Name, Position, attribute columns.
- UX: slider "target archetype" → step-by-step attribute plan.
- Stack: Vue, Node, Postgres, simple knapsack solver (Python).
- Monetization: freemium pro optimizer.
- Complexity: mid-term.
- Risk: not matched to exact game patch levels → stale advice.

3) Custom Build Planner (visual editor)
- What: Drag/drop UI to design a build; live validation against allowed ranges.
- Steps: UI editor → validator uses CSV archetype ranges → export as image/CSV.
- Fields: Build Name (templates), attribute columns, Height, Weight.
- UX: canvas with attribute sliders, "validate" badge.
- Stack: React DnD, Express API, SQLite.
- Monetization: paid templates, print/download.
- Complexity: medium.
- Risk: copyright if using official archetype names in commercial product.

4) Match-Ready Quick Builds (mobile)
- What: Mobile-friendly list of `best-for-mode` builds (MyCAREER, park).
- Steps: tag archetypes for modes → ranking by speed/defense metrics → mobile app list + favorites.
- Fields: Position, Speed/Agility, Perimeter Defense, Threepoint Shot, Driving Layup.
- UX: "For Park" filter → top 10 with one-tap copy.
- Stack: React Native, Firebase.
- Monetization: sponsorships, affiliate links to microtransactions guides.
- Complexity: quick win.
- Risk: recommending builds for paid game modes may touch TOS.

CONTENT & COMMUNITY
5) Build-of-the-Week feed + analytics
- What: Weekly curated build + short meta analysis and stat visual.
- Steps: choose top archetype → create short writeup + radar chart → schedule post.
- Fields: Build Name, Position, top 6 attributes.
- UX: email/Discord post + embedded chart image.
- Stack: Next.js, cron job, Chart.js.
- Monetization: sponsorship, Patreon tier for deep dives.
- Complexity: quick win.
- Risk: content accuracy vs patch updates.

6) YouTube Shorts script generator (build showcase)
- What: Auto-generate short scripts and key stat overlays for creators.
- Steps: pick build → produce 30s script template + stat overlay order → provide PNG assets.
- Fields: Build Name, Strength, Speed, Driving Dunk, Threepoint Shot.
- UX: Download ZIP with overlay assets + script lines.
- Stack: Node, templating, Canvas generation.
- Monetization: tool subscriptions for creators.
- Complexity: quick win.
- Risk: derivative content copyright if using official branding.

7) Community build voting + leaderboards
- What: Users submit custom builds (based on CSV archetypes) & vote.
- Steps: submission form → store builds → ranking algorithm & weekly winners.
- Fields: Build Name, Position, attribute set.
- UX: leaderboard, upvote + comments.
- Stack: Django, Postgres, Redis.
- Monetization: premium votes, sponsored prizes.
- Complexity: mid-term.
- Risk: user content moderation required.

8) Interactive guide hub (role-specific learning paths)
- What: Guided tutorials for each archetype ("How to play Rim Runner").
- Steps: map archetypes → create 4-step guides → embed example lineups and drills.
- Fields: Build Name, Speed, Vertical, Driving Layup, Driving Dunk, Defensive Rebound.
- UX: checklist + embedded drills video list.
- Stack: Gatsby, Markdown CMS.
- Monetization: premium guide bundles.
- Complexity: mid-term.
- Risk: instructional accuracy — needs playtesting.

DATA PRODUCTS & APIs
9) Build Search API (filterable)
- What: API to search builds by position, height range, playstyle tokens.
- Steps: ingest CSVs into DB → build query layer with filters → paginate results.
- Fields: Build Name, Position, Height, all attributes.
- UX: JSON results with archetype matches (example endpoint provided below).
- Stack: FastAPI, Postgres, SQLAlchemy.
- Monetization: paid API keys for higher rate limits.
- Complexity: quick win.
- Risk: throughput/abuse; license for public data.

10) Recommendation API (similar builds)
- What: Given a build, return nearest N archetypes by attribute similarity.
- Steps: compute normalized vectors → cosine similarity index → API endpoint.
- Fields: attribute columns (exclude Height/Weight or encode).
- UX: JSON: [ {build, score, differences} ].
- Stack: Python, Annoy/FAISS, REST.
- Monetization: tiered API.
- Complexity: mid-term.
- Risk: semantic mismatch due to range intervals in CSV.

11) Build Comparison Microservice
- What: Side-by-side comparison with delta highlighting and badge suggestions.
- Steps: normalize attributes → compute deltas & thresholds → render UI/JSON.
- Fields: all attribute columns, Build Name.
- UX: comparison table; recommended badges/upgrades.
- Stack: Node, React, Redis cache.
- Monetization: integration licensing for content sites.
- Complexity: quick win.
- Risk: unfair comparisons if CSV ranges represent multiple sub-variants.

12) Playstyle Search (semantic)
- What: Search by natural language ("fast rim-runner who can shoot").
- Steps: embed archetype descriptions → build small semantic index → map queries to filters.
- Fields: Build Name, Position, attribute columns, free-text playstyle tokens (from source .md).
- UX: search box → recommended archetypes + confidence.
- Stack: Open-source embeddings, Flask, SQLite.
- Monetization: premium ranking signals.
- Complexity: mid-term.
- Risk: embedding drift across patches.

COMPETITIVE & COACHING TOOLS
13) Match Simulator (2-lineups)
- What: Simulate team match outcomes using archetype stats.
- Steps: map attributes to skill weights → Monte Carlo sim → present win-probabilities and key matchups.
- Fields: all attribute columns, Offensive/Defensive rebound, Speed.
- UX: pick two lineups → run simulation → timeline + heatmap.
- Stack: Python (NumPy), Flask, D3 for visualization.
- Monetization: SaaS for coaches/crews.
- Complexity: long.
- Risk: oversimplification of player skill/skill ceilings.

14) Scout Report Generator
- What: Printable PDF scouting reports per opponent archetype.
- Steps: build template → summarize strengths/weaknesses using thresholds → generate PDF.
- Fields: Build Name, Perimeter Defense, Steal, Block, Threepoint Shot, Speed.
- UX: PDF with play recommendations and counters.
- Stack: Node, Puppeteer, Postgres.
- Monetization: paid downloads for competitive teams.
- Complexity: mid-term.
- Risk: inaccuracies in live competition environments.

15) Counter-Build Finder
- What: Given an opponent build, propose counter archetypes.
- Steps: define matchup rule set → run pairwise comparisons → output ranked counters.
- Fields: all attribute columns, Position.
- UX: "Upload opponent build" → top 5 counters with rationale.
- Stack: Python rules engine, Redis.
- Monetization: coaching subscriptions.
- Complexity: mid-term.
- Risk: rules become stale with meta changes.

16) Lineup Chemistry Tool
- What: Detect redundant/weak combos across five chosen builds.
- Steps: normalize attributes → cluster complementary roles → score chemistry.
- Fields: Position, Pass Accuracy, Ball Handle, Speed, Defensive Rebound.
- UX: drag-builds into lineup → chemistry score + replacement suggestions.
- Stack: React, Python analytics.
- Monetization: in-app purchases of pro suggestions.
- Complexity: mid-term.
- Risk: ambiguous "chemistry" definition.

MONETIZABLE SERVICES
17) SaaS Build Management (teams/clubs)
- What: Team portal to manage approved builds, share scout notes, export rosters.
- Steps: multi-tenant DB → user roles → export/import.
- Fields: Build Name, Position, all attributes.
- UX: team dashboard + roster export CSV.
- Stack: Rails or Django, Postgres.
- Monetization: subscription tiers.
- Complexity: long.
- Risk: PII and billing compliance.

18) Premium Build Packs (curated archetypes)
- What: Packaged high-performing builds (playstyle+badges) sold as digital content.
- Steps: curate pack → create landing + delivery → license terms.
- Fields: Build Name, attributes, example usage tips.
- UX: purchase page → download ZIP.
- Stack: Shopify/Stripe + static asset delivery.
- Monetization: direct sales.
- Complexity: quick win.
- Risk: value perception and game updates breaking packs.

19) Sponsored In-Game Advice (affiliate)
- What: Monetize by linking to microtransaction guides or affiliate offers.
- Steps: integrate tracking links → add contextual suggestions when recommending paid content.
- Fields: Build Name, Playstyle.
- UX: contextual CTA "optimize build (sponsored)".
- Stack: any web app + affiliate platform.
- Monetization: referral fees.
- Complexity: quick win.
- Risk: FTC disclosure & user trust.

20) White-label API for content creators
- What: Provide build search and comparison endpoints with custom branding.
- Steps: build API, onboarding docs, SLA.
- Fields: all attributes.
- UX: API key + sample code.
- Stack: FastAPI + Docker + Postgres + Stripe.
- Monetization: subscription + usage.
- Complexity: mid-term.
- Risk: rate-limiting & billing disputes.

RESEARCH & ANALYTICS
21) Archetype Clustering & Taxonomy
- What: Cluster builds to discover new archetypes and remove duplicates.
- Steps: numeric vectorization → clustering (KMeans/HDBSCAN) → name clusters + example reps.
- Fields: attribute columns, Position, Height.
- UX: cluster map + representative builds.
- Stack: Python, scikit-learn, Jupyter notebooks.
- Monetization: consulting, research reports.
- Complexity: mid-term.
- Risk: noisy ranges in CSV (need normalization).

22) Balance Testing Dashboard (patch simulation)
- What: Simulate attribute changes impact on archetype distribution and match outcomes.
- Steps: version-controlled dataset → scenario runner → comparative visuals.
- Fields: all attribute columns.
- UX: slider for attribute delta → live charts.
- Stack: Streamlit/Plotly, Postgres.
- Monetization: tools for modders/researchers.
- Complexity: long.
- Risk: misuse for exploiting live game.

23) Patch Impact Report (Automated)
- What: After a patch, auto-flag archetypes most affected by stat cap/changes.
- Steps: ingest patch changes → compute deltas → issue report.
- Fields: all attributes.
- UX: PDF/HTML report emailed to subscribers.
- Stack: Python pipelines, cron.
- Monetization: paid alerts.
- Complexity: mid-term.
- Risk: dependency on external patch data accuracy.

24) Popularity / Meta Tracker
- What: Track which archetypes are trending (cross-ref with community data).
- Steps: ingest community submissions/votes → time-series analysis → trend alerts.
- Fields: Build Name, Position.
- UX: charts + "fastest rising" lists.
- Stack: Kafka/Redis for events, Postgres.
- Monetization: sponsorship/ads.
- Complexity: mid-term.
- Risk: privacy when ingesting user data.

ML & ADVANCED FEATURES
25) Build Performance Prediction (ML)
- What: Predict in-match performance (points/usage/defense) given attributes.
- Steps: collect labeled play data (requires external data) → train model → expose predict endpoint.
- Fields: all attribute columns + external match labels (not in CSV).
- UX: predicted stat line + confidence.
- Stack: Python, scikit-learn/XGBoost, REST.
- Monetization: premium predictions.
- Complexity: long.
- Risk: requires labeled match data; potential GDPR issues.

26) Similarity Model (FAISS)
- What: Vector embeddings for builds to find nearest neighbors fast.
- Steps: normalize vectors → index with FAISS → implement nearest search API.
- Fields: attribute columns.
- UX: "Find similar archetypes" button → returns list with scores.
- Stack: Python, FAISS, FastAPI.
- Monetization: API quotas.
- Complexity: mid-term.
- Risk: range-based attributes need careful normalization.

27) Auto-Tagging / Semantic Enrichment
- What: Derive playstyle tags (rim-runner, stretch-five) from attributes using classifier.
- Steps: label seed set from CSV names → train lightweight classifier → apply enrichment pipeline.
- Fields: Build Name (seed), attribute columns.
- UX: search by tags, tag suggestions for new builds.
- Stack: Python, scikit-learn.
- Monetization: data licensing.
- Complexity: mid-term.
- Risk: label noise from human-named archetypes.

28) Counterfactual Testing Engine
- What: Ask "if we raise Vertical by 5, how changes expected?" via causal-ish model.
- Steps: build surrogate model → perturb attributes → show delta predictions.
- Fields: attributes used by prediction model (see #25).
- UX: attribute slider + delta preview.
- Stack: Python, PyTorch or XGBoost.
- Monetization: high-tier research product.
- Complexity: long.
- Risk: causal claims may be unsupported.

VISUALIZATIONS & EXPERIENTIAL
29) Interactive Radar / Spider charts explorer
- What: Compare builds visually with spider charts and delta overlays.
- Steps: load build vectors → render interactive radar → support exporting PNG.
- Fields: attribute columns (top 8 chosen).
- UX: select 2-4 builds → interactive overlay + export.
- Stack: React, D3/Plotly.
- Monetization: premium export/branding.
- Complexity: quick win.
- Risk: visual misinterpretation of ranges.

30) 3D/AR Build Visualizer (experimental)
- What: Map attributes to a 3D avatar and motion demo in AR (height, vertical, speed).
- Steps: map attributes→ parametric 3D avatar → WebAR viewer.
- Fields: Height, Speed, Vertical, Strength, Agility.
- UX: scan marker → see 3D animated archetype.
- Stack: Three.js, WebXR, node backend.
- Monetization: branded AR experiences.
- Complexity: long.
- Risk: high development cost; licensing for in-game likeness.

