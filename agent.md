You are an elite product designer, frontend engineer, and personal-brand strategist. Your task is to completely overhaul my portfolio website into a polished, memorable, pixel-art / 8-bit themed experience while preserving a professional academic/research identity.

You have access to Figma and web app development plugins. Use them aggressively:
- Use Figma for UI/UX planning, layout exploration, component design, visual hierarchy, and pixel-art styling.
- Use web app tools to inspect, redesign, implement, test, and polish the live/frontend code.
- Treat this as a full product redesign, not a minor visual refresh.

Core Direction
I want to convert my traditional portfolio website into a pixel-art / 8-bit inspired portfolio. The theme should feel like:
- University of Florida / Gator identity
- swampy / forest / nature environment
- retro game UI
- research + technology 
- professional enough for professors, labs, recruiters, and technical collaborators

The website should feel like entering a “Gator Swamp Quest” portfolio world: playful, but still credible.

Primary Goal
Redesign the portfolio so it advertises my strengths clearly:
1. AI / machine learning research experience
2. Computer science and software development ability
3. Interdisciplinary background connecting technology, and research
4. Recent hands-on experiences including research, projects, and academic work
5. My ability to build useful systems, not just complete assignments

Personal Brand Positioning
Position me as:

“A UF student building at the intersection of AI, software engineering,  and real-world research.”

The tone should be sharp, ambitious, and grounded. Do not make it sound generic or inflated. Avoid startup-bro language. Avoid empty claims like “passionate innovator” unless backed by concrete examples.

Key Experiences to Feature
Use these as the basis for the content architecture. Do not invent fake dates, companies, awards, or metrics. If a detail is unknown, use a clean placeholder or TODO.

1. AI Research Assistant — OOD Detection / Attribution Maps
- Research focus: using attribution maps, especially Integrated Gradients, for out-of-distribution detection.
- Worked with ResNet models, CIFAR/ImageNet-style workflows, Captum Integrated Gradients, binary classifiers, attribution-map datasets, AUROC/AUPRC/F1/confusion matrix style evaluation.
- Recent direction: simplifying OOD/ID experiments using bird ID classes vs vehicle OOD classes to understand whether attribution maps can distinguish meaningful distribution shifts.
- Emphasize: experimental design, model evaluation, ML debugging, research iteration, data pipeline thinking.

2. Software / ML Projects
Feature projects such as:
- OOD / ID Attribution Map Research Pipeline
- ProSol or logic/game-learning app concept
- Gator Gabber Spanish AI conversation partner
- Plants vs. Zombies RL / coach-guided reinforcement learning project
- Delivery Driver Tip Tracker / Tkinter + Excel automation
- Ocean Odyssey Pygame project
- Etch-A-Sketch web app

For each project, the redesigned site should communicate:
- What problem it solves
- What I built
- Tools used
- What I learned
- Why it matters


Connect this to the technical identity:
“I bring real-world domain experience into technical problem solving.”

4. Technical Skills
Organize skills by category, not a giant list.

Suggested categories:
- Machine Learning: PyTorch, ResNet, Integrated Gradients, Captum, model evaluation, classification, OOD detection
- Programming: Python, JavaScript, HTML/CSS, C++, React if applicable
- Data / Tools: pandas, NumPy, matplotlib, Excel automation, OpenPyXL, Git/GitHub
- Research: experiment design, ablation thinking, metric analysis, literature review

Visual Design Requirements
The redesign must follow an 8-bit / pixel-art aesthetic while staying usable.

Theme:
- Gator swamp / forest / retro-game interface
- Pixelated UI cards
- Tilemap-inspired sections
- Retro game dialogue boxes
- Pixel buttons
- Quest-log style project cards
- XP/stat bars for skills
- Inventory-style tool/technology section
- Boss-level or dungeon-style featured projects
- Swamp trail / map progression for timeline or experience

Suggested Visual Motifs:
- Pixel gator avatar
- Swamp water
- cattails
- mossy trees
- lily pads
- fireflies
- 8-bit stars
- UF orange/blue accents, but do not overuse them
- dark forest background with readable content panels

UI/UX Requirements
The new portfolio must be easy to navigate and professional.

Required sections:
1. Hero Section
   - Pixel-art intro scene
   - Clear name/title
   - Short positioning statement
   - CTA buttons: View Projects, View Research, Contact Me

2. About / Character Profile
   - Present me like a player profile or character card
   - Include interdisciplinary angle: AI/software

3. Featured Research
   - Make AI/OOD research a primary section
   - Explain it clearly for both technical and non-technical visitors
   - Include methodology, tools, current phase, and impact

4. Projects / Quest Log
   - Use quest cards
   - Each project should have title, description, tech stack, status, and links
   - Highlight 3–5 strongest projects first

5. Experience Timeline / Swamp Trail
   - Use a game-map/timeline metaphor
   - Include research, vet tech/assistant experience, academic milestones, and major projects

6. Skills / Inventory
   - Categorized inventory grid
   - Use icons or pixel-item cards
   - Avoid meaningless progress bars unless there is a clear reason

7. Contact / Final Checkpoint
   - Email, GitHub, LinkedIn, resume link if available
   - Clear CTA: “Let’s build something useful” or similar, but keep it professional

Interaction Design
Add polished but restrained interactions:
- Pixel hover animations
- Button press effects
- Subtle parallax or floating fireflies
- Section transitions
- Optional keyboard/game-inspired navigation if practical
- Do not sacrifice accessibility or performance for gimmicks

Accessibility Requirements
The site must remain accessible:
- Strong color contrast
- Keyboard navigability
- Semantic HTML
- Alt text for images
- Clear focus states
- Mobile responsive
- Avoid tiny unreadable pixel fonts for body text
- Pixel font can be used for headings/buttons only if readable

Technical Requirements
Before implementing, inspect the existing codebase and determine:
- Current framework
- Existing file structure
- Current styling approach
- Existing content
- Deployment assumptions

Then produce a redesign plan before editing code.

Implementation rules:
- Preserve existing working functionality unless intentionally replacing it.
- Do not remove important content without replacing it with stronger content.
- Prefer clean component architecture.
- Keep performance reasonable.
- Avoid over-engineering.
- Make the site responsive across desktop, tablet, and mobile.
- Use CSS animations carefully.
- Ensure the final version builds successfully.

Content Rules
Rewrite weak or generic portfolio copy into stronger, concrete copy.

Bad:
“I am passionate about technology and animals.”

Better:
“I build software and ML systems informed by real research workflows and hands-on animal care experience.”

Bad:
“I worked on AI research.”

Better:
“I research whether attribution maps from neural networks can help distinguish in-distribution images from out-of-distribution samples, using ResNet models, Integrated Gradients, and binary evaluation pipelines.”

Do not exaggerate. Do not claim published papers, production deployments, awards, or internships unless they already exist in the source material.

Design Deliverables
First, create a design strategy:
- Overall concept
- Sitemap
- Visual language
- Component list
- Color palette
- Typography recommendation
- Animation plan
- Accessibility considerations

Then, create or update the Figma design:
- Desktop homepage
- Mobile homepage
- Core components
- Hero section
- Project card
- Research section
- Timeline section
- Contact section

Then implement the frontend:
- Update layout
- Update styling
- Add interactions
- Improve content
- Ensure responsiveness
- Run build/lint/tests if available

Final Output
When done, provide:
1. Summary of major redesign decisions
2. Files changed
3. New components created
4. How to run the site locally
5. Any TODOs that require my personal input, such as exact resume link, LinkedIn URL, GitHub URL, or missing project links

Critical Standard
This should not look like a generic portfolio with a pixel font slapped on top. It should feel intentionally designed: a professional research/software portfolio expressed through a cohesive 8-bit Gator swamp interface.