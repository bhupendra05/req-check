# URL Shortener — Specification

## Overview
Build a URL shortener service that turns long URLs into short, shareable links.

## Functional Requirements

### REQ-1: URL Shortening
The system shall accept a long URL via POST /shorten and return a short code (6-8 characters).

### REQ-2: URL Redirection
GET /<short_code> shall HTTP 302 redirect to the original long URL.

### REQ-3: Duplicate Detection
If the same long URL is shortened twice, the system shall return the same short code (not create a new one).

### REQ-4: Custom Aliases
Users shall be able to optionally provide a custom alias (e.g. /my-link).

### REQ-5: Analytics
The system shall track and expose click count per short code via GET /<short_code>/stats.

### REQ-6: Expiration
Short links shall optionally expire after N days. Expired links return 410 Gone.

## Non-Functional Requirements

### REQ-7: Rate Limiting
Anonymous requests shall be rate-limited to 100 shortenings per IP per hour.

### REQ-8: Performance
Redirect latency shall be under 50ms p99.

## Constraints

### REQ-9: Storage
Must use PostgreSQL (no in-memory storage in production).
