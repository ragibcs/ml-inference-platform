import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const inferenceDuration = new Trend('inference_latency_ms');
const totalRequests = new Counter('total_http_requests');

// Progressive Stress Profile: 10 -> 25 -> 50 -> 100 -> 200 VUs
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Baseline traffic
    { duration: '1m', target: 25 },   // Early scale
    { duration: '1m', target: 50 },   // Moderate load (HPA trigger point)
    { duration: '2m', target: 100 },  // High concurrency (scale to 6-8 pods)
    { duration: '2m', target: 200 },  // Maximum stress (scale to 10 pods)
    { duration: '1m', target: 50 },   // Traffic drop (scale-down observation)
    { duration: '1m', target: 0 },    // Cool-down to zero
  ],
  thresholds: {
    'http_req_failed': ['rate<0.05'], // Allow up to 5% failure during extreme stress limits
    'error_rate': ['rate<0.05'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

const sampleVectors = [
  [5.1, 3.5, 1.4, 0.2],
  [4.9, 3.0, 1.4, 0.2],
  [6.0, 2.9, 4.5, 1.5],
  [5.7, 2.8, 4.1, 1.3],
  [6.9, 3.1, 5.4, 2.1],
  [6.7, 3.1, 5.6, 2.4],
];

export default function () {
  const vector = sampleVectors[Math.floor(Math.random() * sampleVectors.length)];
  const payload = JSON.stringify({
    features: vector,
    request_id: `stress-${__VU}-${__ITER}`,
  });

  const res = http.post(`${BASE_URL}/predict`, payload, {
    headers: {
      'Content-Type': 'application/json',
      'X-Stress-Test': 'true',
    },
    timeout: '5s',
  });

  totalRequests.add(1);

  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'prediction returned': (r) => r.json() && typeof r.json().prediction === 'number',
  });

  errorRate.add(!success);

  if (res.status === 200 && res.json() && res.json().inference_time_ms) {
    inferenceDuration.add(res.json().inference_time_ms);
  }

  // Tight pacing to generate continuous high RPS pressure
  sleep(0.05);
}
