// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const controllerPath = path.resolve('static/js/timer_controller.js');

function loadControllerClass() {
  if (window.__TimerController__) {
    return window.__TimerController__;
  }
  const source = fs.readFileSync(controllerPath, 'utf-8');
  window.eval(`${source}\nwindow.__TimerController__ = TimerController;`);
  return window.__TimerController__;
}

describe('TimerController', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-04-17T10:00:00Z'));
    window.requestAnimationFrame = (cb) => setTimeout(cb, 16);
    window.cancelAnimationFrame = (id) => clearTimeout(id);
  });

  it('start で idle -> running になる', () => {
    const TimerController = loadControllerClass();
    const state = {
      mode: 'work', status: 'idle', totalSeconds: 1500, remainingSeconds: 1500, endAt: null,
    };
    const store = {
      getState: () => ({ ...state }),
      setState: (partial) => Object.assign(state, partial),
      persist: () => {},
      recordSession: () => {},
    };
    const api = { recordEvent: () => Promise.resolve({}) };
    const notif = { notify: () => {}, playSound: () => {} };

    const controller = new TimerController(store, api, notif);
    controller.start();

    expect(state.status).toBe('running');
    expect(typeof state.endAt).toBe('string');
  });

  it('pause で running -> paused になる', () => {
    const TimerController = loadControllerClass();
    const endAt = new Date(Date.now() + 1200 * 1000).toISOString();
    const state = {
      mode: 'work', status: 'running', totalSeconds: 1500, remainingSeconds: 1500, endAt,
    };
    const store = {
      getState: () => ({ ...state }),
      setState: (partial) => Object.assign(state, partial),
      persist: () => {},
      recordSession: () => {},
    };
    const api = { recordEvent: () => Promise.resolve({}) };
    const notif = { notify: () => {}, playSound: () => {} };

    const controller = new TimerController(store, api, notif);
    controller.pause();

    expect(state.status).toBe('paused');
    expect(state.endAt).toBeNull();
  });
});
