# Changelog

All notable changes to Tennis ELO will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Head-to-head record integration
- Serve/return ELO splits
- Injury and momentum modifiers
- Web interface
- REST API endpoint

### Under Consideration
- Live match predictions
- Betting market comparison
- Player similarity clustering
- Historical data backfill (pre-2020)

---

## [1.0.0] - 2026-03-16

### ✨ Added

#### Core Features
- Surface-adjusted ELO predictions (hard, clay, grass)
- Sample-size calibrated yELO weighting (seasonal form)
- Robust player name resolution system
  - 8,055+ aliases for 895 players
  - Fuzzy matching with typo tolerance
  - Nickname support (e.g., "Djoko" → "Djokovic")
- ATP + WTA tournament support
- Win probability calculation with confidence levels

#### Data
- 895 players (516 ATP, 379 WTA)
- 50 tournaments (Grand Slams, Masters 1000, etc.)
- 722 career ELO records
- 565 seasonal yELO records
- Weekly automated data refresh from Tennis Abstract

#### Infrastructure
- Python package structure (src/ layout)
- Automated CI/CD pipeline
- Unit test suite
- Comprehensive documentation
- MIT License

### 🔧 Changed
- N/A (Initial release)

### 🐛 Fixed
- N/A (Initial release)

### 📝 Documentation
- README.md with installation and usage guide
- API reference documentation
- Contributing guidelines
- Development work log

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-03-16 | Initial release with core features |

---

## Release Notes

### Version 1.0.0 (2026-03-16)

**Highlights:**
- Production-ready prediction engine
- Research-based ELO formula implementation
- Multi-source data integration ready
- Professional Python package structure

**Known Issues:**
- None (initial release)

**Upgrade Notes:**
- N/A (initial release)

---

[Unreleased]: https://github.com/yourusername/tennis-elo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/tennis-elo/releases/tag/v1.0.0
