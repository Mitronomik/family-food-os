// Internal development only. No arbitrary upstream or wildcard proxy.
const config = {
  poweredByHeader: false,
  async rewrites() {
    return [
      { source: "/api/households/:id", destination: "http://127.0.0.1:8000/api/households/:id" },
      { source: "/api/households/:id/members/:member/food-exclusions", destination: "http://127.0.0.1:8000/api/households/:id/members/:member/food-exclusions" },
      { source: "/api/food-ingredients", destination: "http://127.0.0.1:8000/api/food-ingredients" },
      { source: "/api/food-ingredients/:id", destination: "http://127.0.0.1:8000/api/food-ingredients/:id" },
    ];
  },
  async headers() {
    return [{ source: "/:path*", headers: [
      { key: "Cache-Control", value: "no-store" },
      { key: "X-Robots-Tag", value: "noindex, nofollow" },
      { key: "Referrer-Policy", value: "no-referrer" },
    ] }];
  },
};
export default config;
