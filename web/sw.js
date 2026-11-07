// 화면 틀은 저장해 두고, 시세 자료(data.js)는 항상 새로 받는다. 인터넷이 없으면 마지막 자료를 보여 준다.
const CACHE = "legend-v1";
const SHELL = ["./", "index.html", "manifest.json", "icon-192.png", "icon-512.png",
  "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  // 네트워크 먼저, 실패하면 저장본
  e.respondWith(
    fetch(e.request).then((res) => {
      if (res.ok && (e.request.url.startsWith(self.location.origin) || e.request.url.includes("cdnjs"))) {
        const copy = res.clone();
        const key = e.request.url.includes("data.js") ? new URL("data.js", self.location).href : e.request;
        caches.open(CACHE).then((c) => c.put(key, copy));
      }
      return res;
    }).catch(() => caches.match(e.request.url.includes("data.js") ? new URL("data.js", self.location).href : e.request))
  );
});
