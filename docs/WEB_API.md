# Web API contract

The React studio calls the Python server through the `/api` Vite proxy during
development. Start the backend on port `8000`; the production server can also
serve `web/dist` directly.

All API responses are JSON with `Content-Type: application/json`. Successful
responses use HTTP 200. Request validation and execution errors use HTTP 400
with `{"status":"error","message":"..."}`. Unknown API routes use HTTP 404;
unexpected server failures use HTTP 500 with the same error shape.

## Routes

| Method | Route | Request | Successful response |
| --- | --- | --- | --- |
| GET | `/api/health` | none | `status`, `platform`, `version`, and live `workers` count |
| GET | `/api/cluster` | none | `workers[]` with id, host, status, task count, cores, and heartbeat |
| GET | `/api/benchmarks` | none | `scaling[]` and `fusion` benchmark results |
| POST | `/api/compile` | `{code, opt_level?, topology?}` | compiler metrics, equivalence, and compiled `qasm` |
| POST | `/api/run` | `{code, backend?, shots?, seed?}` | backend metadata, counts, probabilities, and amplitudes when available |
| POST | `/api/distributed/run` | `{code, shots?, seed?}` | job id, counts, probabilities, expectation, confidence interval, and recovery events |
| POST | `/api/verify` | `{type}` | verification results for `metamorphic`, `fault_injection`, or differential mode |
| POST | `/api/cptp/validate` | `{channel, param}` | channel parameters and CPTP validation data |

The frontend uses [api.ts](../web/src/api.ts) for all requests. It checks
status and content type, rejects empty or malformed responses, preserves
structured backend messages, and renders failures in the application instead
of using browser alerts.
