import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Target host is parameterized so this script can point at any environment
// without editing code — defaults to the app running on the host via ./start.sh.
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Custom metric tracking failed business-logic checks (as opposed to raw HTTP
// transport failures, which k6's built-in http_req_failed already covers).
const checkFailureRate = new Rate('check_failure_rate');

export const options = {
  // Smoke/load test: ramp 10 VUs up, hold briefly, ramp back down — 1 minute total.
  stages: [
    { duration: '20s', target: 10 }, // ramp-up
    { duration: '20s', target: 10 }, // steady load
    { duration: '20s', target: 0 }, // ramp-down
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'], // fewer than 1% of requests may fail
    http_req_duration: ['p(95)<500'], // 95% of requests must complete under 500ms
    check_failure_rate: ['rate<0.01'],
  },
};

const COUNTRY_CODES = ['IN', 'US', 'GB'];

function randomCountry() {
  return COUNTRY_CODES[Math.floor(Math.random() * COUNTRY_CODES.length)];
}

export default function () {
  const country = randomCountry();

  group('calculate SIP maturity', function () {
    const payload = JSON.stringify({
      monthly_investment: 5000,
      annual_return_rate: 12,
      years: 10,
      country_code: country,
      include_inflation_adjustment: true,
    });

    const res = http.post(`${BASE_URL}/api/calculate`, payload, {
      headers: { 'Content-Type': 'application/json' },
      tags: { endpoint: 'calculate' },
    });

    const ok = check(res, {
      'status is 200': (r) => r.status === 200,
      'has maturity_value': (r) => {
        try {
          return typeof r.json('maturity_value') === 'number';
        } catch {
          return false;
        }
      },
    });
    checkFailureRate.add(!ok);
  });

  group('read inflation info', function () {
    const res = http.get(`${BASE_URL}/api/inflation/${country}`, {
      tags: { endpoint: 'inflation' },
    });

    const ok = check(res, {
      'status is 200': (r) => r.status === 200,
    });
    checkFailureRate.add(!ok);
  });

  group('read suggested rate', function () {
    const res = http.get(`${BASE_URL}/api/suggested-rate/${country}`, {
      tags: { endpoint: 'suggested-rate' },
    });

    const ok = check(res, {
      'status is 200': (r) => r.status === 200,
    });
    checkFailureRate.add(!ok);
  });

  sleep(1); // think time between iterations
}
