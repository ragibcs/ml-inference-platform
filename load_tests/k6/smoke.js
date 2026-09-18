import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const predictionDuration = new Trend('prediction_duration_ms');

// Test configuration: 10 VUs for 1 minute
export const options = {
  vus: 10,
  duration: '1m',
  thresholds: {
    'http_req_failed': ['rate<0.01'],             // Less than 1% errors
    'http_req_duration': ['p(95)<100', 'p(99)<200'], // 95% of requests under 100ms
    'error_rate': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

const sampleFeaturesList = [
  [5.1, 3.5, 1.4, 0.2], // Setosa
  [6.0, 2.9, 4.5, 1.5], // Versicolor
  [6.9, 3.1, 5.4, 2.1], // Virginica
  [4.9, 3.0, 1.4, 0.2], // Setosa
];

export default function () {
  // 1. Health Check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'health body contains healthy': (r) => r.json().status === 'healthy',
  });

  // 2. Prediction Request
  const randomFeatures = sampleFeaturesList[Math.floor(Math.random() * sampleFeaturesList.length)];
  const payload = JSON.stringify({
    features: randomFeatures,
    request_id: `k6-smoke-${__VU}-${__ITER}`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const predictRes = http.post(`${BASE_URL}/predict`, payload, params);
  const success = check(predictRes, {
    'predict status is 200': (r) => r.status === 200,
    'predict has valid confidence': (r) => r.json().confidence >= 0.5,
    'predict has model_version': (r) => r.json().model_version === 'v1.0.0',
    'predict has target_class': (r) => typeof r.json().target_class === 'string',
  });

  errorRate.add(!success);
  if (predictRes.status === 200 && predictRes.json().inference_time_ms) {
    predictionDuration.add(predictRes.json().inference_time_ms);
  }

  sleep(0.5);
}
