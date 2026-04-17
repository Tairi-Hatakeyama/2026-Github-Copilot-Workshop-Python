/**
 * timer_store.js
 * ブラウザ側の状態管理。LocalStorage への保存・復元を担う。
 */

const STORAGE_KEY = 'pomodoro_state';
const SESSIONS_KEY = 'pomodoro_sessions';

class TimerStore {
  constructor() {
    this.state = {
      mode: 'work',
      status: 'idle',
      endAt: null,
      remainingSeconds: 25 * 60,
      totalSeconds: 25 * 60,
      sessionCount: 0,
      startedAt: null,
    };
    this._listeners = [];
  }

  getState() {
    return { ...this.state };
  }

  setState(partial) {
    this.state = { ...this.state, ...partial };
    this._listeners.forEach(fn => fn(this.getState()));
  }

  subscribe(listener) {
    this._listeners.push(listener);
    return () => {
      this._listeners = this._listeners.filter(fn => fn !== listener);
    };
  }

  persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
    } catch (_) { /* ストレージが使えない環境では無視 */ }
  }

  restore() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw);
      // running 状態で復元した場合、既に終了時刻を過ぎていれば idle に戻す
      if (saved.status === 'running' && saved.endAt) {
        const remaining = Math.max(0, Math.floor((new Date(saved.endAt) - Date.now()) / 1000));
        saved.remainingSeconds = remaining;
        if (remaining <= 0) saved.status = 'idle';
      }
      this.state = { ...this.state, ...saved };
    } catch (_) { /* 破損データは無視 */ }
  }

  recordSession(mode) {
    try {
      const sessions = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
      sessions.push({ mode, completedAt: new Date().toISOString() });
      localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    } catch (_) {}
  }

  getTodayStats() {
    try {
      const today = new Date().toDateString();
      const sessions = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
      return sessions
        .filter(s => new Date(s.completedAt).toDateString() === today)
        .reduce(
          (acc, s) => {
            acc.count++;
            if (s.mode === 'work') acc.focusedMinutes += 25;
            return acc;
          },
          { count: 0, focusedMinutes: 0 }
        );
    } catch (_) {
      return { count: 0, focusedMinutes: 0 };
    }
  }
}
