# TODO List - Admin & Analytics Dashboard

Track progress of implementing the secure self-hosted Admin & Analytics Dashboard for the blog.

## Step 1: Implement Page View Tracking in template.html [x]
- [x] Implement `getViews`, `trackView`, and fallback methods in `template.html`'s `dbBridge`.
- [x] Add throttled view tracking invocation on page load (15-minute throttle via localStorage).

## Step 2: Create dashboard.html [x]
- [x] Establish secure login screen (SHA-256 for `admin123`).
- [x] Design responsive glassmorphic dashboard UI using existing themes.
- [x] Integrate Chart.js CDN and fetch view/like/comment stats dynamically from Firebase/localStorage.
- [x] Build live comment moderation list with delete actions.

## Step 3: Automate Post Updates [x]
- [x] Run `python3 update_posts.py` to compile the new template into all 26 articles.

## Step 4: Verification and Quality Control [x]
- [x] Verify page view counts increment when visiting articles.
- [x] Verify security of dashboard.html password prompt.
- [x] Verify visual correctness of charts.
- [x] Verify comment moderation delete action.

## Step 5: Fix Admin Password Issue [x]
- [x] Correct the SHA-256 hash constant in `dashboard.html` for `admin123`
- [x] Add the pure JS SHA-256 fallback function for non-secure contexts (`file://`)
- [x] Verify that password authentication works in both secure contexts and `file://`

## Step 6: Transition to 100% Real Analytics [x]
- [x] Modify `getDeterministicBaseLikes` and `getDeterministicBaseViews` to return `0` in `template.html`
- [x] Modify `getDeterministicBaseLikes` and `getDeterministicBaseViews` to return `0` in `dashboard.html`
- [x] Compile all blog post/writeup pages using `update_posts.py`
- [x] Run automated verification script to confirm base counts are 0 across templates, dashboard, and generated files

## Step 7: Improve TTS Audio / Voice Quality [x]
- [x] Add HTML voice selector dropdown inside the audio player controls in `template.html`
- [x] Implement `populateVoices` to load and priority-sort natural/neural/Google English voices
- [x] Update `initTTS` to apply the user's selected voice
- [x] Compile blog posts and write-ups using `update_posts.py`
- [x] Verify functionality via automated and manual check

