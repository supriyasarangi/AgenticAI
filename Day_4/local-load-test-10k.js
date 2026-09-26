import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const checkFailureRate = new Rate('check_failure_rate');

export const options = {
  scenarios: {
    views: {
      executor: 'shared-iterations',
      vus: 100,
      iterations: 10000,
      maxDuration: '10m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
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

  sleep(0.2);
}
