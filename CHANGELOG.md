# Changelog

## [0.3.0] - 2026-05-25

### Added
- VOS disruption/roadworks monitoring for GMH-relevant public transport notices.
- Sensors for relevant VOS disruption count and latest relevant disruption.
- Problem binary sensor for current relevant VOS traffic disruption.
- Documentation for the VOS source, filtering criteria and maintenance findings.

### Changed
- Version bumped to 0.3.0.

## [0.2.0] - 2026-05-24

### Fixed
- Train direction filtering now uses prefix matching instead of substring matching, preventing false matches (e.g. "Bielefeld" no longer matches "Bielefeld West" unintentionally)

### Added
- HTTP request timeouts on all network calls (30 s default, 10 s for link checks, 120 s for the BNetzA CSV download, 10 s for camera snapshots) — prevents hung coordinator refreshes
- Exponential-backoff retry logic (up to 2 retries) for transient network errors in all data sources
- AWIGO address validation during integration setup — invalid addresses are reported immediately in the config flow instead of only on first coordinator refresh
- Camera URL validation during setup — rejects non-HTTP/HTTPS values with a clear error message
- German error messages in `strings.json` for config-flow validation failures
- HACS validation and Home Assistant hassfest checks in CI/CD
- `codeowners` field in `manifest.json`

### Changed
- `NLWKN_SUBSCRIPTION_KEY` documented as a public read-only key for the NLWKN BIS governmental water-level API
- Exception types in `check_link_sources` and `_current_csv_url` narrowed from bare `Exception` to `(aiohttp.ClientError, asyncio.TimeoutError, OSError)`
- Version bumped to 0.2.0

## [0.1.0] - 2026-05-24

Initial public release.
