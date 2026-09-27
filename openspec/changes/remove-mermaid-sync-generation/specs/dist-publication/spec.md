## MODIFIED Requirements

### Requirement: Scheduled generation publishes through a pull request
Any automated job that regenerates content under `plugins/` SHALL run the full build afterwards and SHALL open a pull request carrying the source and `dist/` changes together — no direct pushes to the default branch. The pull request SHALL pass the standard CI gate before merge.

#### Scenario: Automated generation opens a combined PR
- **WHEN** an automated content-generation job changes files under `plugins/`
- **THEN** it opens a pull request containing those changes together with the corresponding re-rendered files under both `dist/` trees
