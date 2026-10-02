import http from 'k6/http';
import { check } from 'k6';

export const options = { stages: [{ duration: '30s', target: 50 }, { duration: '1m', target: 200 }, { duration: '30s', target: 0 }] };
const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export function setup() {
  const r = http.post(`${BASE}/api/links`, JSON.stringify({ url: 'https://example.com' }), { headers: { 'content-type': 'application/json' } });
  return { code: r.json('code') };
}

export default function (d) {
  const r = http.get(`${BASE}/${d.code}`, { redirects: 0 });
  check(r, { 'is 307': (x) => x.status === 307 });
}
