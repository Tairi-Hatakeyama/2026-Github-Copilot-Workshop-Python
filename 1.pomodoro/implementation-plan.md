# ポモドーロタイマー - 段階的実装計画

## 📋 計画基本方針

- **層の実装順序**: ドメイン層 → API層 → フロントエンド層
- **テスト駆動**: 各段階でユニットテストを並行して実装
- **マイルストーン**: 各スプリント終了時に動作確認できる状態を目指す
- **段階的統合**: 下層の変更は上層に影響を最小化する

---

## 🔧 Sprint 0: 基盤整備（1-2日）

プロジェクト構造の確立とローカル環境の構築

### フェーズ 0.1: ディレクトリ構造とファイル作成
**目標**: プロジェクト構造を実装可能な状態に整える

- [ ] `1.pomodoro/domain/` ディレクトリの作成
  - [ ] `__init__.py` の作成
  - [ ] `models.py` - データモデル定義（Mode, Status, SessionState）
  - [ ] `events.py` - イベント定義（TimerEvent, 各イベントクラス）
  - [ ] `timer.py` - タイマー制御ロジック

- [ ] `1.pomodoro/services/` ディレクトリの作成
  - [ ] `__init__.py` の作成
  - [ ] `config_service.py` - 設定管理
  - [ ] `stats_service.py` - 統計管理

- [ ] `1.pomodoro/tests/` ディレクトリの作成
  - [ ] `__init__.py` の作成
  - [ ] `conftest.py` - pytest 設定
  - [ ] `test_models.py`
  - [ ] `test_timer.py`
  - [ ] `test_api.py`

- [ ] `1.pomodoro/templates/` ディレクトリの作成
  - [ ] `index.html` - 基本のHTMLテンプレート

- [ ] `1.pomodoro/static/` ディレクトリの作成
  - [ ] `css/style.css` - スタイルシート
  - [ ] `js/app.js` - アプリケーション初期化
  - [ ] `js/timer_store.js` - 状態管理
  - [ ] `js/timer_controller.js` - タイマー制御
  - [ ] `js/notification_service.js` - 通知処理

### フェーズ 0.2: 依存パッケージの準備
**目標**: 開発環境の整備

- [ ] `requirements.txt` ファイルの作成（Flask, pytest など）
- [ ] 仮想環境の構築と有効化
- [ ] パッケージのインストール
- [ ] 簡単な動作確認（Flaskアプリが起動することを確認）

### フェーズ 0.3: 基本的なFlaskアプリケーション
**目標**: App Factoryパターンでの最小構成

- [ ] `1.pomodoro/app.py` - App Factory実装
  - [ ] `create_app(config=None)` 関数
  - [ ] ルートエンドポイント `/` で index.html を返す
  - [ ] エラーハンドラーの基本設定
  
- [ ] ローカルサーバの起動確認（ブラウザでアクセス可能な状態）

**マイルストーン**: Flask アプリが起動し、ブラウザから http://localhost:5000 にアクセス可能

---

## 🎯 Sprint 1: ドメイン層のコア実装（2-3日）

タイマーの状態遷移とロジックを実装。テストを並行して実装。

### フェーズ 1.1: データモデルの定義
**目標**: 型安全で拡張性のあるモデルを実装

**実装内容**: `domain/models.py`

```python
# 定義対象
- Enum: Mode (WORK, BREAK)
- Enum: Status (IDLE, RUNNING, PAUSED)
- Dataclass: SessionState
  - current_mode: Mode
  - current_status: Status
  - remaining_seconds: int
  - end_at: Optional[datetime]
  - paused_at: Optional[datetime]
  - session_count: int
- Dataclass: TimerConfig
  - work_minutes: int = 25
  - break_minutes: int = 5
```

**テスト対象**:
- [ ] モデルのインスタンス化
- [ ] デフォルト値の確認
- [ ] 不正な値での例外発生

### フェーズ 1.2: イベント定義
**目標**: イベント駆動型の設計を実現

**実装内容**: `domain/events.py`

```python
# 定義対象
- Abstract: TimerEvent
- Classes: 
  - StartEvent
  - PauseEvent
  - ResumeEvent
  - ResetEvent
  - CompleteEvent
```

**テスト対象**:
- [ ] 各イベントのインスタンス化
- [ ] イベントの属性確認

### フェーズ 1.3: タイマーロジックの実装（ステップ1: 初期化と基本遷移）
**目標**: 状態遷移の基本フレームワーク完成

**実装内容**: `domain/timer.py`

```python
# Clock依存を注入可能な設計
class Clock:
    def now() -> datetime: ...

class SystemClock(Clock):
    def now() -> datetime:
        return datetime.now()

# ドメインロジック（純粋関数）
def handle_event(
    current_state: SessionState,
    event: TimerEvent,
    config: TimerConfig,
    clock: Clock
) -> SessionState:
    """
    現在状態 + イベント → 次状態
    副作用指示も返す（別の関数で）
    """
    # 状態遷移のロジックを記述
```

**遷移対象**（優先度順）:

1. [ ] `idle + start -> running`
   - 実装: 終了予定時刻を計算、status を RUNNING に
   - テスト: 開始時に end_at が正しく計算されること

2. [ ] `running + pause -> paused`
   - 実装: 残り秒を計算、status を PAUSED に
   - テスト: 一時停止時に remaining_seconds が正確に保存されること

3. [ ] `paused + resume -> running`
   - 実装: 保存済み remaining_seconds から新しい end_at を計算
   - テスト: 再開時に残り時間が復元されること

4. [ ] `<any> + reset -> idle`
   - 実装: status を IDLE に、remaining_seconds をリセット
   - テスト: リセット後の状態が初期状態と同一

5. [ ] `running + complete -> break (or work)`
   - 実装: タイマー満了時に次モードへ遷移
   - テスト: work 完了時に break の state になること

### フェーズ 1.4: 時間計算ロジックの実装
**目標**: 精密な時間計算（遅延に強い設計）

**実装内容**: `domain/timer.py` に追加

```python
# 時間計算用の純粋関数
def calculate_remaining_seconds(
    end_at: datetime,
    clock: Clock
) -> int:
    """終了予定時刻から現在時刻の差分を秒単位で返す"""
    ...

def calculate_progress_percentage(
    remaining_seconds: int,
    total_seconds: int
) -> float:
    """進捗率を 0.0 ～ 1.0 で返す"""
    ...
```

**テスト対象**:
- [ ] 残り時間の計算精度
- [ ] 進捗率の計算
- [ ] レッドケース: 終了時刻を過ぎた場合の動作（0 を返す）

### フェーズ 1.5: ドメイン層の統合テスト
**目標**: ユーザーシナリオを網羅するテスト

**テストシナリオ**:
- [ ] シナリオ1: 開始 → 完了 → 一時停止できない
- [ ] シナリオ2: 開始 → 一時停止 → 再開 → 完了
- [ ] シナリオ3: 開始 → リセット → 初期状態に戻る
- [ ] シナリオ4: 開始後、システム時刻が戻った場合の処理
- [ ] シナリオ5: Work 完了後、Break モードに遷移
- [ ] シナリオ6: Break 完了後、Work モードに遷移

**マイルストーン**: ドメイン層の全テストがパスし、状態遷移が確定

---

## 🔌 Sprint 2: API層の実装（2-3日）

Flaskアプリで提供するエンドポイントを実装

### フェーズ 2.1: 設定サービスの実装
**目標**: 設定の読み書きを抽象化

**実装内容**: `services/config_service.py`

```python
# インターフェース
class ConfigStore(ABC):
    def get_config() -> TimerConfig: ...
    def save_config(config: TimerConfig) -> None: ...

# 実装
class InMemoryConfigStore(ConfigStore):
    # テスト用、メモリに保存
    
class FileConfigStore(ConfigStore):
    # JSONファイルに保存（将来的には SQLite へ）
```

**テスト対象**:
- [ ] 設定の取得・保存が動作する
- [ ] デフォルト値が正しい

### フェーズ 2.2: 統計サービスの実装
**目標**: 統計情報の記録と集計

**実装内容**: `services/stats_service.py`

```python
# インターフェース
class StatsStore(ABC):
    def add_session(event_type: str, completed_at: datetime) -> None: ...
    def get_today_stats() -> DailyStats: ...
    def get_stats_range(start: date, end: date) -> List[DailyStats]: ...

# 実装
class InMemoryStatsStore(StatsStore):
    # テスト用
    
class FileStatsStore(StatsStore):
    # JSONファイルに保存
```

**テスト対象**:
- [ ] セッション記録
- [ ] 日単位の集計
- [ ] 統計の取得

### フェーズ 2.3: APIエンドポイントの実装（ステップ1: 基本エンドポイント）
**目標**: 必要な API を実装

**実装内容**: `app.py` に追加

1. [ ] **GET /api/config**
   - レスポンス: `{ "work_minutes": 25, "break_minutes": 5 }`
   - テスト: 設定値が正しく返される

2. [ ] **PUT /api/config**
   - リクエスト: `{ "work_minutes": 30, "break_minutes": 7 }`
   - レスポンス: 更新後の設定
   - テスト: 
     - [ ] 正常系：設定が更新される
     - [ ] 異常系：不正な値での validation error

3. [ ] **GET /api/stats/today**
   - レスポンス: 
   ```json
   {
     "date": "2026-04-17",
     "completed_work_sessions": 3,
     "completed_break_sessions": 2,
     "focused_minutes": 75
   }
   ```
   - テスト: 統計情報が正しく返される

4. [ ] **POST /api/stats/events**
   - リクエスト: `{ "event_type": "work_completed", "completed_at": "..." }`
   - レスポンス: `{ "status": "recorded" }`
   - テスト: イベントが記録される

### フェーズ 2.4: エラーハンドリングの実装
**目標**: 堅牢なAPI

**実装内容**: `app.py`

- [ ] 400 Bad Request: 不正入力
- [ ] 404 Not Found: 存在しないエンドポイント
- [ ] 500 Internal Server Error: 予期しないエラー
- [ ] JSON形式のエラーレスポンス

**テスト対象**:
- [ ] 各ステータスコード
- [ ] エラーレスポンス形式

### フェーズ 2.5: APIテストの実装
**目標**: テストで API の動作を保証

**テスト対象**: `tests/test_api.py`

- [ ] 各エンドポイントの正常系テスト
- [ ] バリデーション異常系テスト
- [ ] 状態遷移後の API レスポンス確認

**マイルストーン**: API エンドポイントが全て動作し、テストがパス

---

## 🎨 Sprint 3: フロントエンド基本実装（3-4日）

UIの基本構成と状態管理の実装

### フェーズ 3.1: HTMLテンプレートの構築
**目標**: セマンティックで拡張性のあるHTML

**実装内容**: `templates/index.html`

```html
<!-- 実装対象 -->
- <div class="timer-display">
  - 現在モード表示（Work / Break）
  - タイマー表示（MM:SS）
  - 進捗インジケーター（進捗バー）
  
- <div class="controls">
  - 開始ボタン（id: btn-start）
  - 一時停止ボタン（id: btn-pause）
  - リセットボタン（id: btn-reset）
  
- <div class="stats-panel">
  - 本日の完了セッション数
  - 本日の集中時間
  
- <div class="notification-status">
  - 通知許可状態表示
  - 通知許可ボタン
```

**テスト対象**:
- [ ] HTML が妥当な構造か（HTMLバリデーター）
- [ ] 必要な id/class が存在するか

### フェーズ 3.2: CSSスタイリング（モバイルファースト）
**目標**: レスポンシブで視認性の高いデザイン

**実装内容**: `static/css/style.css`

**基本スタイル**:
- [ ] モバイル（320px～）: 縦積みレイアウト
  - タイマー大きく表示
  - ボタン縦並び
  
- [ ] タブレット（768px～）: 2段レイアウト
  - 左にタイマー、右に統計
  
- [ ] デスクトップ（1024px～）: 3段レイアウト
  - 中央にタイマー、両側にコントロール
  
**コンポーネント**:
- [ ] タイマー表示: 大きく見やすいフォント（最低 48pt）
- [ ] ボタン: タッチしやすいサイズ（最低 44×44px）
- [ ] 進捗バー: 視認が容易な色彩（作業時と休憩時で異なる色）
- [ ] 統計パネル: 見落としやすくないサイズ

**アニメーション**:
- [ ] 状態遷移時のスムーズな色変わり
- [ ] ボタン押下時のフィードバック

### フェーズ 3.3: 状態ストアの実装
**目標**: ブラウザ側の状態管理

**実装内容**: `static/js/timer_store.js`

```javascript
// TimerStore クラス
class TimerStore {
  constructor() {
    this.state = {
      mode: "work",      // work / break
      status: "idle",    // idle / running / paused
      endAt: null,       // 終了予定時刻（ISO文字列）
      remainingSeconds: 1500, // 25分 = 1500秒
      totalSeconds: 1500,
      sessionCount: 0,
      startedAt: null
    }
    this.listeners = [];
  }
  
  // 状態を取得
  getState() { ... }
  
  // 状態を更新
  setState(newState) { ... }
  
  // 状態変更を監視
  subscribe(listener) { ... }
  
  // LocalStorage に保存
  persist() { ... }
  
  // LocalStorage から復元
  restore() { ... }
}
```

**テスト対象**:
- [ ] 状態の読み取り
- [ ] 状態の更新
- [ ] リスナーの登録と呼び出し
- [ ] LocalStorage の保存と復元

### フェーズ 3.4: タイマーコントローラーの実装
**目標**: ブラウザ側のタイマー制御

**実装内容**: `static/js/timer_controller.js`

```javascript
class TimerController {
  constructor(store, apiClient, clock = systemClock) {
    this.store = store;
    this.apiClient = apiClient;
    this.clock = clock;
    this.intervalId = null;
  }
  
  // タイマー開始
  start() { ... }
  
  // タイマー一時停止
  pause() { ... }
  
  // タイマー再開
  resume() { ... }
  
  // タイマーリセット
  reset() { ... }
  
  // 定期的に時間を更新（requestAnimationFrame）
  tick() { ... }
  
  // 精密な残り時間計算
  calculateRemaining() { ... }
}
```

**テスト対象**:
- [ ] 各ボタン操作に対する状態遷移
- [ ] 残り時間の計算精度
- [ ] 完了時の判定

### フェーズ 3.5: アプリケーション初期化
**目標**: 画面起動時の準備処理

**実装内容**: `static/js/app.js`

```javascript
// ページロード時に実行
document.addEventListener('DOMContentLoaded', () => {
  // ストア初期化
  const store = new TimerStore();
  store.restore(); // LocalStorage から復元
  
  // API クライアント初期化
  const apiClient = new ApiClient();
  
  // コントローラー初期化
  const controller = new TimerController(store, apiClient);
  
  // ボタンイベント登録
  document.getElementById('btn-start').addEventListener('click', () => {
    controller.start();
  });
  // ... 他のボタン
  
  // 状態変更時の画面更新
  store.subscribe((newState) => {
    updateDisplay(newState);
  });
  
  // ティック開始
  controller.startTicking();
  
  // 設定読み込み
  loadConfig();
});
```

### フェーズ 3.6: 画面表示更新処理
**目標**: 状態に合わせた画面更新

**実装内容**: `static/js/app.js` に追加

```javascript
function updateDisplay(state) {
  // タイマー表示の更新
  const minutes = Math.floor(state.remainingSeconds / 60);
  const seconds = state.remainingSeconds % 60;
  document.getElementById('timer-display').textContent = 
    `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  
  // モード表示の更新
  document.getElementById('mode-display').textContent = 
    state.mode === 'work' ? 'Work' : 'Break';
  
  // ボタン状態の更新
  updateButtonStates(state.status);
  
  // 進捗バーの更新
  const progress = (state.totalSeconds - state.remainingSeconds) / state.totalSeconds * 100;
  document.getElementById('progress-bar').style.width = `${progress}%`;
  
  // LocalStorage に保存
  store.persist();
}

function updateButtonStates(status) {
  document.getElementById('btn-start').disabled = status === 'running';
  document.getElementById('btn-pause').disabled = status !== 'running';
  document.getElementById('btn-reset').disabled = status === 'idle';
}
```

**マイルストーン**: ボタン操作で状態が遷移し、画面が更新される状態

---

## 🔔 Sprint 4: 通知と統計機能（2-3日）

ブラウザ通知とサウンド、統計表示を実装

### フェーズ 4.1: 通知サービスの実装
**目標**: ブラウザ通知とサウンド再生

**実装内容**: `static/js/notification_service.js`

```javascript
class NotificationService {
  constructor() {
    this.permission = Notification.permission;
  }
  
  // 通知権限を要求
  async requestPermission() { ... }
  
  // ブラウザ通知を表示
  notify(title, options = {}) { ... }
  
  // サウンドを再生
  playSound(soundType = 'complete') { ... }
}
```

**テスト対象**:
- [ ] 通知を表示できる
- [ ] サウンドを再生できる
- [ ] 権限なしでエラーハンドリングされる

### フェーズ 4.2: タイマー完了時の通知
**目標**: タイマー満了時に通知とサウンドが発火する

**実装内容**: `static/js/timer_controller.js` に追加

```javascript
// 完了判定と通知
if (this.store.state.remainingSeconds <= 0) {
  // API へイベント記録
  this.apiClient.recordEvent(
    this.store.state.mode === 'work' ? 'work_completed' : 'break_completed'
  );
  
  // 通知実行
  const notifService = new NotificationService();
  notifService.notify(
    `${this.store.state.mode === 'work' ? 'Work' : 'Break'} Complete!`,
    { body: 'Next session starting soon...' }
  );
  
  // サウンド再生
  notifService.playSound('complete');
  
  // 次セッションへ遷移（またはアイドル状態へ）
  this.transitionToNext();
}
```

### フェーズ 4.3: 統計表示の実装
**目標**: 本日の成績を表示

**実装内容**: `templates/index.html` + `static/js/app.js`

**HTML**:
```html
<div class="stats-panel">
  <h3>Today's Stats</h3>
  <div class="stat-item">
    <span>Sessions:</span>
    <span id="stat-sessions">0</span>
  </div>
  <div class="stat-item">
    <span>Focused Time:</span>
    <span id="stat-focused-time">0 min</span>
  </div>
</div>
```

**JavaScript**:
```javascript
async function loadStats() {
  const response = await fetch('/api/stats/today');
  const stats = await response.json();
  
  document.getElementById('stat-sessions').textContent = 
    stats.completed_work_sessions;
  document.getElementById('stat-focused-time').textContent = 
    `${stats.focused_minutes} min`;
}
```

**テスト対象**:
- [ ] 統計データの読み込み
- [ ] 表示の更新
- [ ] API との連携

### フェーズ 4.4: LocalStorage への統計保存
**目標**: ブラウザ側での統計情報保持

**実装内容**: `static/js/timer_store.js` に追加

```javascript
// セッション完了時に記録
recordSession(mode) {
  const session = {
    mode,
    completedAt: new Date().toISOString(),
    duration: this.state.totalSeconds
  };
  
  const sessions = JSON.parse(localStorage.getItem('sessions')) || [];
  sessions.push(session);
  localStorage.setItem('sessions', JSON.stringify(sessions));
}

// 本日の統計を計算
getTodayStats() {
  const today = new Date().toDateString();
  const sessions = JSON.parse(localStorage.getItem('sessions')) || [];
  
  return sessions
    .filter(s => new Date(s.completedAt).toDateString() === today)
    .reduce((acc, s) => {
      acc.count++;
      if (s.mode === 'work') acc.focusedMinutes += s.duration / 60;
      return acc;
    }, { count: 0, focusedMinutes: 0 });
}
```

**マイルストーン**: タイマー完了時に通知とサウンドが発火し、統計が表示される

---

## 🎯 Sprint 5: UI磨きとテスト充実（2-3日）

レスポンシブ対応を完全化し、テストカバレッジを高める

### フェーズ 5.1: レスポンシブ対応の完成
**目標**: モバイル/タブレット/デスクトップで快適に使用可能

**実装内容**: `static/css/style.css` 拡張

- [ ] 480px ブレークポイント: モバイルサイズ対応
  - ボタンを大きく（44×44px 以上）
  - 余白を適切に調整
  
- [ ] 768px ブレークポイント: タブレット対応
  - 2段レイアウト対応
  - 統計パネルを横並び
  
- [ ] 1024px ブレークポイント: デスクトップ対応
  - 3段レイアウト対応
  - 情報の整理

**テスト対象**:
- [ ] ブラウザのデベロッパーツールで各サイズでの表示確認

### フェーズ 5.2: フロントエンドロジックテストの充実
**目標**: JavaScript のロジックテストを実装

**テスト対象** (Jest または Mocha):
- [ ] TimerStore の状態管理
- [ ] TimerController の時間計算
- [ ] 状態遷移のロジック
- [ ] 通知の条件判定

### フェーズ 5.3: E2E シナリオテスト
**目標**: ユーザーの利用フロー全体をテスト

**手動テストシナリオ**:
- [ ] シナリオ1: 開始から完了まで（25分のカウントダウン）
- [ ] シナリオ2: 中断と再開
- [ ] シナリオ3: リセット操作
- [ ] シナリオ4: 複数セッション後の統計表示
- [ ] シナリオ5: ブラウザ再起動後の状態復元
- [ ] シナリオ6: モバイルでの操作性確認

### フェーズ 5.4: パフォーマンス最適化
**目標**: 快適な動作

- [ ] JavaScript バンドルサイズの確認
- [ ] requestAnimationFrame の効率化
- [ ] LocalStorage のサイズ確認
- [ ] CSS アニメーションの最適化

### フェーズ 5.5: アクセシビリティ対応
**目標**: 視覚障害者など、様々なユーザーが使用可能

- [ ] ARIA ラベルの追加
- [ ] キーボード操作の対応
- [ ] 色覚異常への対応
- [ ] スクリーンリーダー対応

**マイルストーン**: 本番環境へのデプロイが可能な品質を達成

---

## ✅ 各セッションでの検証項目

### Sprint 1 完了時の検証
- [ ] `pytest tests/test_timer.py` でユニットテストが全パス
- [ ] すべての状態遷移が期待通り機能する
- [ ] 時間計算に遅延の影響がないか確認

### Sprint 2 完了時の検証
- [ ] `pytest tests/test_api.py` でAPIテストが全パス
- [ ] Postman/curl で各エンドポイントが動作確認
- [ ] エラーハンドリングが適切に機能

### Sprint 3 完了時の検証
- [ ] ボタン操作で画面が更新される
- [ ] LocalStorage に状態が保存される
- [ ] ブラウザリロード後に状態が復元される

### Sprint 4 完了時の検証
- [ ] タイマー完了時に通知が表示される
- [ ] サウンドが再生される
- [ ] 統計情報が記録・表示される

### Sprint 5 完了時の検証
- [ ] モバイル/タブレット/デスクトップで快適に使用可能
- [ ] テストカバレッジが 80% 以上
- [ ] パフォーマンスが許容範囲内

---

## 📊 実装困難度と時間目安

| Sprint | フェーズ | 困難度 | 時間目安 |
|--------|---------|--------|---------|
| 0 | 基盤整備 | ⭐ 低 | 1-2日 |
| 1.1-1.2 | モデル・イベント定義 | ⭐ 低 | 0.5日 |
| 1.3-1.4 | タイマーロジック | ⭐⭐⭐ 高 | 1.5日 |
| 1.5 | 統合テスト | ⭐⭐ 中 | 1日 |
| 2.1-2.4 | API 実装 | ⭐⭐ 中 | 2日 |
| 2.5 | APIテスト | ⭐ 低 | 1日 |
| 3.1-3.3 | HTML/CSS | ⭐⭐ 中 | 1.5日 |
| 3.4-3.6 | JavaScript実装 | ⭐⭐⭐ 高 | 2.5日 |
| 4.1-4.4 | 通知・統計 | ⭐⭐ 中 | 1.5日 |
| 5.1-5.5 | UI磨き・テスト | ⭐⭐ 中 | 1.5日 |

**総時間目安**: 14～18日（1日4-6時間の作業として）

---

## 🚀 並行実装のポイント

- Sprint 1（ドメイン層）と Sprint 2（API層）は依存関係があるため、順序を守る
- Sprint 2 と Sprint 3 は若干並行可能（API スタブを使って進める）
- Sprint 4 と Sprint 5 は Sprint 3 完了後に並行可能

---

## 👥 複数人での分業案

**チーム3名の場合**:
- **バックエンド担当**: Sprint 1 → Sprint 2
- **フロントエンド担当**: Sprint 3 → Sprint 4 の前半
- **品質担当**: 各スプリントのテスト実装と E2E テスト

**チーム1名の場合**:
提案の順序通り、Sprint 0 → Sprint 5 へ進める

---

## 📝 補足

- 各フェーズ終了時に `git commit -m "Sprint X.Y: <フェーズ名>"` でコミット
- テスト駆動開発（TDD）を心がけ、テストコード → 実装の順で進める
- 不測な困難が生じた場合は、各フェーズの粒度を見直す
