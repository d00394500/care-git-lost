# After Hours arcade

Standalone frontend for https://two026-it4200-fall.onrender.com/.
Includes coin flip, roulette, slots, dice, Cross the road, Rocket ride,
fortunes, and an API explorer.
Bets are simulated; no wallet or real money is involved.

## Local preview

Run: python3 dev_server.py
Use python or py if that is your interpreter command. No pip install needed.
Open http://127.0.0.1:8080. Stop with Ctrl+C.

The local server serves public/ and proxies /api/* to the fixed Render backend.
Use this server rather than opening index.html directly or a static-only server.

## Hosting

Import this GitHub repo into Netlify. netlify.toml publishes public/ with no
build command and proxies /api/* to Render. No backend credentials needed.
Netlify has not been connected or deployed by this change.
GitHub Pages alone cannot run the proxy. Other hosts need an equivalent rewrite,
or direct backend requests with CORS enabled for the frontend domain.

## Included files

- public/index.html: arcade page
- public/api-routes.json: endpoint catalog used by the API explorer
- public/arcade.css: responsive styles
- public/arcade.js: games, requests, and explorer
- dev_server.py: local preview and fixed-upstream proxy
- netlify.toml: static hosting and production proxy
- tests/test_frontend.py: assets, catalog, and proxy tests
- .github/workflows/test.yaml: tests and JavaScript syntax check
- .gitignore: generated file exclusions

The endpoint catalog is a snapshot of the Flask source. Update
public/api-routes.json when routes or methods change. Live responses always come
from Render; routes absent from the deployed backend show their error. POST
requests execute real backend operations, including score updates. Render may
need time to wake up after inactivity. Retry timed-out requests.

## Checks

Run: python3 -m unittest discover -s tests -v
Optional JavaScript syntax check: node --check public/arcade.js
Node is supplied by CI; local serving needs only Python 3.12+.
Backend files, dependencies, tests, and release workflows stay in the backend repo.
