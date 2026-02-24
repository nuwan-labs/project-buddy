/* Project Buddy Service Worker */
const CACHE_NAME = 'project-buddy-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    event.waitUntil(
      self.registration.showNotification(event.data.title || 'Project Buddy', {
        body: event.data.message || 'What are you working on?',
        icon: '/vite.svg',
        badge: '/vite.svg',
        requireInteraction: true,
        actions: [
          { action: 'log',   title: 'Log Now' },
          { action: 'snooze', title: 'Snooze 15m' },
          { action: 'skip',  title: 'Skip' },
        ],
      })
    );
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'skip') return;

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      const client = clients.find((c) => c.url && 'focus' in c);
      if (client) {
        client.focus();
        client.postMessage({ type: 'SHOW_ACTIVITY_POPUP' });
      } else {
        self.clients.openWindow('/').then((newClient) => {
          if (newClient) newClient.postMessage({ type: 'SHOW_ACTIVITY_POPUP' });
        });
      }
    })
  );
});
