/**
 * notification_service.js
 * ブラウザ通知とサウンド再生を担う。
 */

class NotificationService {
  constructor() {
    this._permission = typeof Notification !== 'undefined'
      ? Notification.permission
      : 'denied';
  }

  async requestPermission() {
    if (typeof Notification === 'undefined') return;
    this._permission = await Notification.requestPermission();
  }

  notify(title, options = {}) {
    if (this._permission !== 'granted') return;
    try {
      new Notification(title, { icon: '/static/icon.png', ...options });
    } catch (_) {}
  }

  playSound(soundType = 'complete') {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, ctx.currentTime);
      gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);

      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + 0.8);
    } catch (_) {}
  }

  getPermission() {
    return this._permission;
  }
}
