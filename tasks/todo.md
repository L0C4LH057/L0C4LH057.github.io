# TODO List - Blog UI/UX Refactoring

Track progress of refactoring the cybersecurity and AI blog into a premium, futuristic cyberpunk theme.

## Step 1: Design Master Layout & Components [/]
- [/] Update `template.html` with futuristic dark mesh theme, cyberpunk styling, responsive typography, and glassmorphism.
- [ ] Create glowing animated background (Canvas-based particles or keyframe mesh gradients).
- [ ] Refactor the Upvote Button component with micro-animations & particle feedback.
- [ ] Refactor the Share Widget with copy-link animations and native sharing.
- [ ] Refactor the Comments Section to look like a terminal command output / high-tech feed.

## Step 2: Refactor Main Index & Subpages [ ]
- [ ] Update `index.html` to align with the futuristic style, adding a terminal title typing effect and glassmorphic cards.
- [ ] Update `whoami.html` to style the profile page as a developer HUD / security dossier dossier.
- [ ] Update `write-ups.html` to style the writeup list as a cyber-deck CTF log.
- [ ] Update `tools.html` to style the tool cards as glowing system interfaces.

## Step 3: Automate Post Updates [ ]
- [ ] Write `update_posts.py` to parse existing post files, extract content/metadata, and inject them into the new `template.html`.
- [ ] Run the Python script and verify that all posts are updated successfully.

## Step 4: Verification and Quality Control [ ]
- [ ] Run a local web server to check layout, typography, accessibility, and responsiveness.
- [ ] Verify functionality of Firebase upvotes, comments, and sharing.
