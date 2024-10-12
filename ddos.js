import http from "k6/http";
import { check } from 'k6';
import exec from 'k6/execution';

export const options = {
  scenarios: {
    constant_request_rate: {
      executor: 'ramping-arrival-rate',
      preAllocatedVUs: 50,
      timeUnit: '1s',
      startRate: 50,
      stages: [
        { target: 200, duration: '5m' }, // linearly go from 50 iters/s to 200 iters/s for 5m
        { target: 500, duration: '0' }, // instantly jump to 500 iters/s
        { target: 500, duration: '5m' }, // continue with 500 iters/s for 5 minutes
      ],
    },
  },
};

export default function () {
  const uid = `${exec.scenario.iterationInTest}`

  let body = {
    username: uid,
    name: uid,
    birthdate: "2024-10-09T00:00:00",
    password: "password123"
  };

  let res = http.post("http://localhost:8000/user-register", JSON.stringify(body));

  check(res, {
    'status is 200': (r) => r.status === 200,
    'is correct username': (r) => r.json().username === uid,
  });
}
