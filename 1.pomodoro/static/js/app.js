/**
 * app.js
 * 画面初期化・イベントリスナー登録・DOM更新を担う。
 */

document.addEventListener('DOMContentLoaded', () => {
  const store = new TimerStore();
  const notifService = new NotificationService();

  const apiClient = {
    async getConfig() {
      const res = await fetch('/api/config');
      return res.json();
    },
    async putConfig(config) {
      const res = await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      return res.json();
    },
    async getTodayStats() {
      const res = await fetch('/api/stats/today');
      return res.json();
    },
    async recordEvent(event_type) {
      const res = await fetch('/api/stats/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type,
          completed_at: new Date().toISOString(),
        }),
      });
      return res.json();
    },
  };

  const controller = new TimerController(store, apiClient, notifService);

  // LocalStorage から状態を復元
  store.restore();
  updateDisplay(store.getState());

  // ボタンイベント登録
  document.getElementById('btn-start').addEventListener('click', () => {
    const { status } = store.getState();
    if (status === 'idle') controller.start();
    else if (status === 'paused') controller.resume();
  });

  document.getElementById('btn-pause').addEventListener('click', () => {
    controller.pause();
  });

  document.getElementById('btn-reset').addEventListener('click', () => {
    controller.reset();
  });

  document.getElementById('btn-notify-permission').addEventListener('click', async () => {
    await notifService.requestPermission();
    updateNotificationStatus(notifService.getPermission());
  });

  // キーボード操作: Space/Enter で開始・再開、P で一時停止、R でリセット。
  document.addEventListener('keydown', (event) => {
    // 入力欄での誤動作を防止
    const tag = (event.target && event.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || event.target?.isContentEditable) {
      return;
    }

    if (event.code === 'Space' || event.code === 'Enter') {
      event.preventDefault();
      const { status } = store.getState();
      if (status === 'running') {
        controller.pause();
      } else if (status === 'idle') {
        controller.start();
      } else if (status === 'paused') {
        controller.resume();
      }
      return;
    }

    if (event.key.toLowerCase() === 'p') {
      controller.pause();
      return;
    }

    if (event.key.toLowerCase() === 'r') {
      controller.reset();
    }
  });

  // 状態変更時に画面を更新
  store.subscribe((newState) => {
    updateDisplay(newState);
  });

  // タイマーループ開始
  controller.startTicking();

  // 初期データ読み込み
  loadConfig(apiClient, store);
  loadStats(apiClient);
  updateNotificationStatus(notifService.getPermission());
});

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function updateDisplay(state) {
  document.getElementById('timer-display').textContent = formatTime(state.remainingSeconds);

  document.getElementById('mode-display').textContent =
    state.mode === 'work' ? 'Work' : 'Break';

  const progress = state.totalSeconds > 0
    ? ((state.totalSeconds - state.remainingSeconds) / state.totalSeconds) * 100
    : 0;
  document.getElementById('progress-bar').style.width = `${Math.min(100, progress)}%`;

  updateButtonStates(state.status);
}

function updateButtonStates(status) {
  const btnStart = document.getElementById('btn-start');
  const btnPause = document.getElementById('btn-pause');
  const btnReset = document.getElementById('btn-reset');

  btnStart.disabled = status === 'running';
  btnStart.textContent = status === 'paused' ? '再開' : '開始';
  btnPause.disabled = status !== 'running';
  btnReset.disabled = status === 'idle';
}

function updateNotificationStatus(permission) {
  const label = { granted: '許可済み', denied: '拒否済み', default: '未設定' };
  document.getElementById('notification-status-text').textContent =
    `通知: ${label[permission] || '未設定'}`;
  document.getElementById('btn-notify-permission').style.display =
    permission === 'granted' ? 'none' : '';
}

async function loadConfig(apiClient, store) {
  try {
    const cfg = await apiClient.getConfig();
    const workTotal = cfg.work_minutes * 60;
    const breakTotal = cfg.break_minutes * 60;
    const { mode, status } = store.getState();
    store.setState({
      workSeconds: workTotal,
      breakSeconds: breakTotal,
    });
    // 実行中でなければ totalSeconds を設定値に合わせる
    if (status === 'idle') {
      store.setState({
        totalSeconds: mode === 'work' ? workTotal : breakTotal,
        remainingSeconds: mode === 'work' ? workTotal : breakTotal,
      });
    }
  } catch (_) {}
}

async function loadStats(apiClient) {
  try {
    const stats = await apiClient.getTodayStats();
    document.getElementById('stat-sessions').textContent = stats.completed_work_sessions;
    document.getElementById('stat-focused-time').textContent = `${stats.focused_minutes} 分`;
  } catch (_) {}
}
