import http from 'k6/http';

export const options = {
  stages: [
    { duration: '10s', target: 1 },
  ],
};

export default function () {
  http.get('http://localhost:8000/item/1');
}
