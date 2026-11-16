# ProxyShield Advanced Public Proxy Intelligence & Transparency Engine

## Project Objective

Develop an advanced, transparent public-proxy-based network security auditing system.

The tool must use publicly available free proxy endpoints rather than intentionally using the operator's direct public IP for target requests.

Author: Quarkova.

## A. Public Proxy Discovery

Implement a configurable proxy source registry.

Features:

- Support multiple public proxy list providers.
- Import proxy lists from TXT and JSON.
- Support HTTP, HTTPS, SOCKS4 and SOCKS5.
- Record the original source of every proxy.
- Record source URL and retrieval timestamp.
- Validate proxy format.
- Detect duplicate endpoints.
- Maintain a proxy health database.
- Allow manual proxy source configuration.

Never assume public proxy lists are trustworthy.

Respect provider terms, robots policies where applicable, and rate limits.

## B. Proxy Verification

Before using a proxy:

1. Test connectivity.
2. Verify the proxy protocol.
3. Identify the externally observed exit IP using a trusted IP-echo endpoint.
4. Measure latency.
5. Detect connection failures.
6. Verify HTTPS CONNECT support where applicable.
7. Check whether the proxy leaks the direct client IP through HTTP headers.
8. Record verification time.

Never send credentials, cookies or sensitive data through public proxies.

## C. Strict Direct-IP Protection

This is a critical requirement.

Implement a strict proxy-only mode.

- Never send target requests directly when proxy mode is enabled.
- Disable automatic direct connection fallback.
- If the proxy fails, stop the request.
- Verify the observed exit IP before testing the target.
- Reject requests if the observed source IP unexpectedly matches the operator's direct public IP.
- Do not silently change the network route.
- Clearly report proxy failures.

Important: Explain that proxy-only mode cannot guarantee anonymity or prevent all possible metadata leaks.

## D. Multi-Proxy Security Testing

For authorized targets only:

- Select verified public proxy endpoints.
- Perform low-rate HTTP requests.
- Record the observed exit IP.
- Record the target response.
- Identify HTTP 403, 429 and 5xx.
- Detect timeout and connection failures.
- Compare results across proxy endpoints.
- Stop automatically when configured safety limits are reached.

Do not use proxy rotation to evade another server's security controls or bypass rate limits.

## E. Advanced Transparency System

Every proxy must have a record containing:

- Proxy IP.
- Port.
- Protocol.
- Country, if reliably identified.
- ASN.
- ISP.
- Source provider name.
- Source URL.
- First discovered time.
- Last verified time.
- Latency.
- Availability.
- Exit IP verification.
- Anonymity classification.
- Security warnings.
- Number of successful verification attempts.

Every report must disclose which public proxy endpoints were used.

Do not hide proxy providers or silently substitute endpoints.

## F. Firewall Verification

Distinguish these results:

- Proxy connection failure.
- DNS failure.
- TCP connection failure.
- TLS handshake failure.
- HTTP 403.
- HTTP 429.
- HTTP 5xx.
- Successful HTTP response.
- Confirmed firewall block, only when supported by server-side evidence.

For confirmed firewall verification, provide an optional server-side agent that reads authorized firewall logs.

Do not classify every rejected connection as an IP block.

## G. Proxy Risk Analysis

Create a proxy risk scoring engine.

Check:

- Protocol security.
- HTTPS support.
- Unexpected HTTP headers.
- IP mismatch.
- Suspicious proxy behavior.
- Provider reputation where reliable data is available.
- Last verification age.

Label proxies:

- Unverified
- Verified Connectivity
- High Risk
- Unavailable

Do not label an untrusted public proxy as secure simply because it passed connectivity testing.

## H. Advanced Reporting

Support:

- HTML
- JSON
- CSV
- PDF

Include:

1. Total discovered proxies.
2. Total verified proxies.
3. Total unavailable proxies.
4. Proxy provider distribution.
5. Proxy country distribution.
6. Observed exit IPs.
7. Target response distribution.
8. Latency statistics.
9. Firewall verification results.
10. Direct-IP fallback status.
11. Proxy risk warnings.
12. Complete source attribution.

## I. Technical Stack

Python:

- HTTPX
- PySocks
- dnspython
- psutil
- ipaddress
- Rich
- Typer
- Pydantic
- SQLAlchemy
- SQLite
- Jinja2
- Cryptography
- Pytest

Bash:

- Installation
- Environment detection
- Dependency management
- Diagnostics
- Backup and restore

## J. Privacy & Legal Transparency

Display this notice in README and the application:

"ProxyShield uses publicly available third-party proxy services for educational and authorized network security auditing. The operator's direct public IP is not intentionally used for target requests in strict proxy-only mode. Public proxy operators may observe, inspect or log traffic. ProxyShield does not guarantee anonymity, privacy or proxy security. All testing must be conducted against authorized targets."

## K. Final Requirement

The application must be genuinely functional, modular, transparent and testable.

Build a professional public-proxy intelligence and authorized network security auditing platform.

Do not implement unrestricted distributed traffic generation, security-control evasion or unauthorized scanning.
