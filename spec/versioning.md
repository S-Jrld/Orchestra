# Orchestra Versioning Specification

All artifacts in the Orchestra ecosystem follow strict Semantic Versioning (`MAJOR.MINOR.PATCH`):

1. **Specification Version (`spec_version`)**:
   - `MAJOR`: Breaking changes to canonical schema structure or core execution lifecycle.
   - `MINOR`: Backward-compatible schema property additions or new standard adapter capabilities.
   - `PATCH`: Documentation clarifications, schema typo fixes, or non-functional edits.

2. **Skill Manifest Version (`schema_version`)**:
   - Manifests declare `schema_version: "1.0.0"`.
   - Forward compatibility: The runtime ignores unrecognized optional fields if the major version matches, but strictly validates required schema fields.

3. **Skill Release Version (`version`)**:
   - Independent semantic versioning for individual portable skills in `skills/<id>/manifest.json`.
   - Upstream tracking revisions are recorded separately under `source.revision`.

4. **Workflow Definition Version (`version`)**:
   - Workflows in `workflows/` or external packages declare their independent versioning to allow progressive upgrades and reproducible runs.
