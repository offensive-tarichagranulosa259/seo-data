# Third-Party Notices

This file contains the licenses and notices for third-party software used in seo-data.

---

## Table of Contents

- [Google API Clients](#google-api-clients)
- [HTTP Client](#http-client)
- [License Texts](#license-texts)

---

## Google API Clients

### google-api-python-client

- **Package**: google-api-python-client
- **Source**: https://github.com/googleapis/google-api-python-client
- **License**: Apache License 2.0
- **Copyright**: Copyright (c) Google LLC

Used for calling the Google Search Console API and the Google Analytics Admin API (property listing).

### google-auth

- **Package**: google-auth
- **Source**: https://github.com/googleapis/google-auth-library-python
- **License**: Apache License 2.0
- **Copyright**: Copyright (c) Google LLC

Provides the credential and refresh-token primitives used to authenticate Google API calls.

### google-auth-oauthlib

- **Package**: google-auth-oauthlib
- **Source**: https://github.com/googleapis/google-auth-library-python-oauthlib
- **License**: Apache License 2.0
- **Copyright**: Copyright (c) Google LLC

Provides the OAuth 2.0 loopback flow used by `connect_google.py` to obtain user consent.

### google-analytics-data

- **Package**: google-analytics-data
- **Source**: https://github.com/googleapis/python-analytics-data
- **License**: Apache License 2.0
- **Copyright**: Copyright (c) Google LLC

Generated client for the Google Analytics Data API v1beta. Used by `ga4_query.py` to run GA4 reports.

---

## HTTP Client

### requests

- **Package**: requests
- **Source**: https://github.com/psf/requests
- **License**: Apache License 2.0
- **Copyright**: Copyright 2019 Kenneth Reitz

Used by `bing_auth.py` to call the Bing Webmaster Tools REST API.

---

## License Texts

### Apache License 2.0

The full text of the Apache License 2.0 is available at:

https://www.apache.org/licenses/LICENSE-2.0

A copy is also bundled with each of the packages listed above. Unless otherwise stated, the copyright in those packages remains with their respective owners; nothing in this notice transfers ownership.

---

## Service APIs

This project calls the following hosted services via the clients listed above. The terms of those services apply when the skill is used:

- **Google Search Console API** -- https://developers.google.com/webmaster-tools/v1/api_reference_index
- **Google Analytics Data API** -- https://developers.google.com/analytics/devguides/reporting/data/v1
- **Google Analytics Admin API** -- https://developers.google.com/analytics/devguides/config/admin/v1
- **Bing Webmaster Tools API** -- https://learn.microsoft.com/en-us/bingwebmaster/getting-access

The skill does not redistribute Google or Microsoft trademarks, branding, or proprietary content.
