# Lessons Learned - Admin Password Bug Fix

## 1. Web Crypto API Context Limitation
- **Pattern**: Using `crypto.subtle` directly inside frontend JavaScript pages.
- **Problem**: Browsers disable the Web Crypto API (`crypto.subtle`) in insecure contexts (such as opening local files via the `file://` protocol). This causes the hashing function to crash with a `TypeError` (reading properties of undefined).
- **Lesson**: Always implement a pure JavaScript SHA-256 fallback function (e.g. `sha256Fallback`) and check for `window.crypto.subtle` availability before calling it.

## 2. Cryptographic Constant Verification
- **Pattern**: Hardcoding expected hashes.
- **Problem**: Mismatches between generated hashes and expected constants (such as typos or generating from incorrect string formats).
- **Lesson**: Double-check hardcoded hash constants against multiple independent standard hash generators (like Node.js native `crypto`) to ensure they represent the exact intended input.
