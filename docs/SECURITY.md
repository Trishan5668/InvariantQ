# Security policy

## Scope

InvariantQ accepts circuit source and JSON configuration through Python, the
REST server, and the web client. Inputs are parsed as IQ-Lang/qIR and are not
executed as Python. Experiment manifests are JSON-only, schema-validated, and
must contain an explicit circuit string; they do not contain executable code.

Resource exhaustion remains the principal application risk. Callers should
configure memory limits, shot limits, and process isolation for untrusted jobs.
The optional native library is loaded only from the documented package/build
locations and its availability is reported explicitly.

## Reporting

Please report suspected vulnerabilities privately to the repository
maintainers before public disclosure. Include a minimal reproduction, affected
version/commit, platform, and impact. Do not include credentials or private
research data.

## Automated checks

The CI security job runs `pip-audit`, Bandit, and the frontend `npm audit`
command. Scanner findings are evidence to triage, not a proof of security;
unavailable network services or advisories are reported as unverified.
Dependency changes are tested before adoption and optional quantum-framework
dependencies remain outside the core runtime requirements.
