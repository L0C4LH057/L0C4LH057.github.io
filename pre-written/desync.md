## HTTP/1.1 Must Die: Navigating the Desync Endgame and the Horror of Request Smuggling

For over six years, the web security community has warned that **HTTP/1.1 has a fatal flaw**—the fundamental isolation between individual HTTP requests is broken. This systemic failure has led to the persistent threat known as **HTTP Desync Attacks**, primarily executed through **Request Smuggling**.

Despite the development of newer, safer protocols like HTTP/2 and HTTP/3, the continued reliance on HTTP/1.1 for upstream connections routinely exposes millions of websites to catastrophic compromises, including full cache poisoning, credential theft, and session hijacking. Recent research has demonstrated that these techniques could compromise over **30 million websites** by exploiting flaws within major Content Delivery Networks (CDNs).

### The Core Vulnerability: Conflicting Message Lengths

HTTP/1.1 is an old, lenient, text-based protocol where requests are simply concatenated back-to-back over a shared TCP connection. The danger arises because the protocol offers multiple ambiguous ways to define where one message ends and the next begins.

A successful request smuggling attack exploits a tiny **parser discrepancy** between two servers—a front-end proxy (like a load balancer or CDN) and a back-end origin server—regarding the message boundary.

This ambiguity is typically caused by inconsistencies in how servers interpret the two primary length headers:

1.  **`Content-Length` (CL):** Specifies the body size in exact bytes.
2.  **`Transfer-Encoding: chunked` (TE):** Indicates the body is sent in variable chunks, terminating with a zero-length chunk.

The HTTP specification technically prohibits using both headers simultaneously. However, when an attacker provides both, if the front end prioritises one (e.g., CL) and the back end prioritises the other (e.g., TE), a **desynchronization (desync)** occurs. The attacker can then smuggle malicious data that prefixes the next legitimate user's request.

### The Sequel is Worse: The HTTP/2 Downgrade Problem

It was initially thought that moving to **HTTP/2 (H2)** would eliminate request smuggling. H2 is a binary protocol that uses frames, and every frame has its own built-in length measurement, removing the message length ambiguity inherent in H1.

However, the widespread practice of **H2 downgrading** has instead compounded the threat. The vast majority of servers that speak H2 with the client then rewrite or downgrade these requests to H1 to communicate with the back end. This conversion process negates all the security benefits of H2.

Two key H2 downgrade vulnerabilities demonstrate this risk:

1.  **Incorrect Content Length:** Systems like the front end used by Netflix failed to verify that a manually supplied `Content-Length` header in an H2 request was correct. An attacker could supply an incorrect length, causing the downgraded H1 request to be interpreted as 1.5 requests on the back end, successfully smuggling a malicious prefix. This earned a $20,000 bounty for the researcher.

2.  **Connection-Specific Header Bypass:** The H2 RFC states that any message containing connection-specific header fields (such as `Transfer-Encoding: chunked`) **must be treated as malformed**. Amazon’s Application Load Balancer (ALB) and systems using Encapsula’s WAF failed to obey this rule. By sending an H2 request containing the `Transfer-Encoding: chunked` header, the ALB forwarded it, allowing the back end to prioritise TE over the correct CL, causing a desync.

### The Desync Endgame: Bypassing Modern Defenses

Over the last six years, lightweight defenses, often based on WAFs using regular expressions, have been deployed to block common attack *detection* methods (like those using `Transfer-Encoding`) but have not fixed the underlying H1 vulnerability. This necessitates sophisticated, multi-stage attacks.

#### 1. Parser Discrepancy Scanning

Instead of relying on known signatures (which are often blocked), modern detection focuses on **fingerprinting behavioural anomalies**. The **HTTP Request Smuggler version 3** tool uses a parser discrepancy scan by attempting to smuggle subtle malformations.

For example, by using a space to mask a `Host` header—making it visible to the front end but hidden from the back end—a unique server response (like a 403 status code) can reveal a discrepancy that signals vulnerability.

#### 2. Exploiting the Zero-CL Deadlock

For five years, a specific desync scenario—where the front end doesn't see a smuggled `Content-Length` header but the back end does—was considered unexploitable because it resulted in a **zero-CL deadlock**. The back end, expecting a body, would time out waiting for data the front end never sent.

The breakthrough was finding an **early response gadget**. Some servers, like EngineX or Microsoft IIS (when hitting paths like `/con/`), will respond early if the request targets a **static file**, thereby breaking the deadlock.

Once the deadlock is broken, the back end chops off bytes from the next request. To achieve full control, this requires a **double desync** attack: the first attacker request causes the zero-CL desync, which weaponises the second attacker request to cause a CL:0 desync, allowing the arbitrary payload to be prefixed onto the victim's request.

#### 3. High-Impact Attack Primitives

*   **Response Queue Poisoning:** This occurs when the attacker smuggles **exactly two complete requests**. The front end loses track of response ordering, leading to random responses being sent to random users. On Atlassian Jira, this caused users to be persistently logged into random accounts via exposed `Set-Cookie` headers, forcing Atlassian to log out everyone worldwide.

*   **The HEAD Technique (Tunneling):** Used when servers deploy mitigations like AWS Desync Guardian, which refuse to reuse a connection after a suspicious request (Request Tunneling). This attack can also make blind attacks non-blind.
    *   By smuggling a `HEAD` request, the back end responds with headers but **no body**. Crucially, the back end still includes the **`Content-Length` header** for the absent body.
    *   This forces the front end to miscalculate the response length and read into the headers and content of the *next* request’s response, exposing sensitive information or enabling cache poisoning (e.g., compromising Bitbucket for a maximum bounty payout).

*   **The `Expect` Header:** The `Expect` header is an advanced primitive because it forces the request into a two-part process, introducing statefulness into the core logic. Sending this header causes inconsistencies that leak memory (including secret keys) or break front-end attempts to strip sensitive headers. By sending a valid `Expect` header, researchers triggered zero-CL desyncs on numerous targets, including a pre-production server for T-Mobile ($12,000 bounty).

### The Only Solution: HTTP/1.1 Must Die

The perpetual complexity of HTTP/1.1, which serves as an "absolute gold mine for all kinds of research," ensures that more desync attacks are always on the way.

The primary reason HTTP/1.1 cannot be fixed through patches (like aggressive normalization) is that server vendors are unwilling to break backward compatibility with ancient HTTP clients.

Therefore, the only adequate long-term solution is for network architects to **use HTTP/2 or HTTP/3 end-to-end**. By ensuring the origin server supports H2 and enabling upstream H2 on the front end, the protocol's binary framing and robust length measurement resolve the core flaw of request isolation.

While major vendors like EngineX, Akamai, CloudFront, and Fastly need community pressure to adopt upstream H2 support, security experts must continue to demonstrate the severity of the threat.

> "We need to collectively show the world that HTTP 1.1 is insecure and that more desync attacks are always coming."