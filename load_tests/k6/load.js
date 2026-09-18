import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const singleInferenceDuration = new Trend('single_inference_duration_ms');
const batchInferenceDuration = new Trend('batch_inference_duration_ms');
const totalPredictions = new Counter('total_predictions');

// Staged load test profile: 50 -> 100 VUs over 9 minutes
export const options = {
  stages: [
    { duration: '1m', target: 50 },  // Ramp-up to 50 users
    { duration: '3m', target: 50 },  // Steady state at 50 users
    { duration: '1m', target: 100 }, // Ramp-up to 100 users
    { duration: '3m', target: 100 }, // Peak steady state at 100 users
    { duration: '1m', target: 0 },   // Graceful ramp-down
  ],
  thresholds: {
    'http_req_failed': ['rate<0.01'],              // < 1% errors
    'http_req_duration': ['p(95)<250', 'p(99)<500'], // 95% < 250ms, 99% < 500ms
    'error_rate': ['rate<0.01'],
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
  const rand = Math.random();

  // Traffic routing: 80% single predict, 10% batch predict, 10% health/ready
  if (rand < 0.80) {
    // Single Prediction Request
    const vector = sampleVectors[Math.floor(Math.random() * sampleVectors.length)];
    const payload = JSON.stringify({
      features: vector,
      request_id: `load-${__VU}-${__ITER}`,
    });

    const res = http.post(`${BASE_URL}/predict`, payload, {
      headers: { 'Content-Type': 'application/json' },
    });

    const success = check(res, {
      'single predict 200': (r) => r.status === 200,
      'has confidence': (r) => r.json().confidence > 0,
    });

    errorRate.add(!success);
    if (res.status === 200) {
      totalPredictions.add(1);
      if (res.json().inference_time_ms) {
        singleInferenceDuration.add(res.json().inference_time_ms);
      }
    }
  } else if (rand < 0.90) {
    // Batch Prediction Request
    const batchPayload = JSON.stringify({
      instances: [
        sampleVectors[0],
        sampleVectors[2],
        sampleVectors[4],
      ],
    });

    const res = http.post(`${BASE_URL}/predict/batch`, batchPayload, {
      headers: { 'Content-Type': 'application/json' },
    });

    const success = check(res, {
      'batch predict 200': (r) => r.status === 200,
      'batch size is 3': (r) => r.json().batch_size === 3,
    });

    errorRate.add(!success);
    if (res.status === 200) {
      totalPredictions.add(3);
      if (res.json().total_inference_time_ms) {
        batchInferenceDuration.add(res.json().total_inference_time_ms);
      }
    }
  } else {
    // Health & Readiness Probes
    const res = http.get(`${BASE_URL}/ready`);
    const success = check(res, {
      'ready is 200': (r) => r.status === 200,
      'model loaded': (r) => r.json().model_loaded === true,
    });
    errorRate.add(!success);
  }

  // Realistic user think time
  sleep(Math.random() * 0.2 + 0.1);
}
