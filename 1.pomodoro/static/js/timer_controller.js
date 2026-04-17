/**
 * timer_controller.js
 * タイマーの進行制御と状態遷移を担う。
 * 終了予定時刻との差分で残り時間を計算するため、遅延に強い。
 */

class TimerController {
  constructor(store, apiClient, notificationService) {
    this._store = store;
    this._apiClient = apiClient;
    this._notifService = notificationService;
    this._rafId = null;
  }

  start() {
    const { status, mode, totalSeconds } = this._store.getState();
    if (status !== 'idle') return;

    const endAt = new Date(Date.now() + totalSeconds * 1000).toISOString();
    this._store.setState({
      status: 'running',
      endAt,
      startedAt: new Date().toISOString(),
    });
    this._store.persist();
  }

  pause() {
    const { status, endAt } = this._store.getState();
    if (status !== 'running') return;

    const remaining = this._calculateRemaining(endAt);
    this._store.setState({
      status: 'paused',
      remainingSeconds: remaining,
      endAt: null,
    });
    this._store.persist();
  }

  resume() {
    const { status, remainingSeconds } = this._store.getState();
    if (status !== 'paused') return;

    const endAt = new Date(Date.now() + remainingSeconds * 1000).toISOString();
    this._store.setState({ status: 'running', endAt });
    this._store.persist();
  }

  reset() {
    const { mode } = this._store.getState();
    const totalSeconds = this._getModeSeconds(mode);
    this._store.setState({
      status: 'idle',
      endAt: null,
      remainingSeconds: totalSeconds,
      totalSeconds,
      startedAt: null,
    });
    this._store.persist();
  }

  startTicking() {
    const tick = () => {
      this._tick();
      this._rafId = requestAnimationFrame(tick);
    };
    this._rafId = requestAnimationFrame(tick);
  }

  stopTicking() {
    if (this._rafId !== null) {
      cancelAnimationFrame(this._rafId);
      this._rafId = null;
    }
  }

  _tick() {
    const { status, endAt } = this._store.getState();
    if (status !== 'running' || !endAt) return;

    const remaining = this._calculateRemaining(endAt);
    this._store.setState({ remainingSeconds: remaining });

    if (remaining <= 0) {
      this._onComplete();
    }
  }

  _calculateRemaining(endAt) {
    return Math.max(0, Math.floor((new Date(endAt) - Date.now()) / 1000));
  }

  _onComplete() {
    const { mode } = this._store.getState();
    const eventType = mode === 'work' ? 'work_completed' : 'break_completed';

    // API へ記録（失敗しても継続）
    this._apiClient.recordEvent(eventType).catch(() => {});

    // LocalStorage へも記録
    this._store.recordSession(mode);

    // 通知
    const title = mode === 'work' ? '作業完了！' : '休憩終了！';
    const body = mode === 'work' ? '休憩しましょう。' : '次の作業を始めましょう。';
    this._notifService.notify(title, { body });
    this._notifService.playSound('complete');

    this._transitionToNext();
  }

  _transitionToNext() {
    const { mode } = this._store.getState();
    const nextMode = mode === 'work' ? 'break' : 'work';
    const totalSeconds = this._getModeSeconds(nextMode);
    this._store.setState({
      mode: nextMode,
      status: 'idle',
      endAt: null,
      remainingSeconds: totalSeconds,
      totalSeconds,
    });
    this._store.persist();
  }

  _getModeSeconds(mode) {
    const { workSeconds = 25 * 60, breakSeconds = 5 * 60 } = this._store.getState();
    return mode === 'work' ? workSeconds : breakSeconds;
  }
}
