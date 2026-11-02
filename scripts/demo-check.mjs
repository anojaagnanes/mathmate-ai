#!/usr/bin/env node
// Pre-demo readiness check. Makes no inference calls and spends nothing.
// Usage: DEMO_PASSWORD=xxx node scripts/demo-check.mjs you@example.com
const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:3000';
const email = process.argv[2];
const password = process.env.DEMO_PASSWORD;
let failures = 0;
const ok = (name, good, extra = '') => {
  console.log(`${good ? 'PASS' : 'FAIL'} ${name}${extra ? ' — ' + extra : ''}`);
  if (!good) failures++;
};
const health = await fetch(`${BACKEND}/api/v1/health`).then(r => r.json()).catch(() => null);
ok('backend reachable', !!health, health ? JSON.stringify(health) : BACKEND);
if (email && password) {
  const login = await fetch(`${BACKEND}/api/v1/auth/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-MathMate-Client': 'web', Origin: FRONTEND},
    body: JSON.stringify({email, password}),
  }).then(r => r.json()).catch(() => null);
  const token = login && login.access_token;
  ok('login', !!token, token ? `user ${login.user.name}` : 'check email/password');
  if (token) {
    const s = await fetch(`${BACKEND}/api/v1/tutor/status`, {
      headers: {Authorization: 'Bearer ' + token, 'X-MathMate-Client': 'web', Origin: FRONTEND},
    }).then(r => r.json()).catch(() => null);
    ok('tutor status', !!s);
    if (s) {
      console.log(`     provider=${s.provider} model=${s.model} configured=${s.configured} live_verified=${s.live_verified}`);
      console.log(`     requests_remaining=${s.usage.requests_remaining} session_usd=${s.usage.estimated_session_usd}`);
      console.log(s.configured
        ? '     → Meta is ON: rehearse the Meta segment of the demo script.'
        : '     → Meta is OFF: demo runs on the local engine; say so in the video.');
    }
  }
} else {
  console.log('SKIP login/status (pass email arg + DEMO_PASSWORD env to include)');
}
const front = await fetch(FRONTEND, {method: 'HEAD'}).catch(() => null);
ok('frontend reachable', !!front && front.ok, FRONTEND);
console.log(failures ? 'NOT READY' : 'READY');
process.exit(failures ? 1 : 0);
