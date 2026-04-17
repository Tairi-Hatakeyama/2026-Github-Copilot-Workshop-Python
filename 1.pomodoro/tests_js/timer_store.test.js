// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const scriptPath = path.resolve('static/js/timer_store.js');

function loadStoreClass() {
  if (window.__TimerStore__) {
    return window.__TimerStore__;
  }
  const source = fs.readFileSync(scriptPath, 'utf-8');
  // グローバルクラスとして定義されるため window 経由で取り出す。
  window.eval(`${source}\nwindow.__TimerStore__ = TimerStore;`);
  return window.__TimerStore__;
}

describe('TimerStore', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('初期状態が正しい', () => {
    const TimerStore = loadStoreClass();
    const store = new TimerStore();
    const state = store.getState();

    expect(state.mode).toBe('work');
    expect(state.status).toBe('idle');
    expect(state.remainingSeconds).toBe(1500);
  });

  it('setState で状態が更新される', () => {
    const TimerStore = loadStoreClass();
    const store = new TimerStore();

    store.setState({ status: 'running' });
    expect(store.getState().status).toBe('running');
  });

  it('subscribe で変更通知を受け取れる', () => {
    const TimerStore = loadStoreClass();
    const store = new TimerStore();
    let called = false;

    store.subscribe((state) => {
      called = true;
      expect(state.status).toBe('running');
    });

    store.setState({ status: 'running' });
    expect(called).toBe(true);
  });

  it('persist/restore で状態を復元できる', () => {
    const TimerStore = loadStoreClass();
    const store1 = new TimerStore();
    store1.setState({ status: 'paused', remainingSeconds: 1200 });
    store1.persist();

    const store2 = new TimerStore();
    store2.restore();
    expect(store2.getState().status).toBe('paused');
    expect(store2.getState().remainingSeconds).toBe(1200);
  });

  it('recordSession/getTodayStats が動作する', () => {
    const TimerStore = loadStoreClass();
    const store = new TimerStore();

    store.recordSession('work');
    store.recordSession('work');
    const stats = store.getTodayStats();

    expect(stats.count).toBe(2);
    expect(stats.focusedMinutes).toBe(50);
  });
});
