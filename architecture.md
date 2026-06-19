# Architecture
## Overview
既存の FastAPI TODO API に、追加のビルド工程を必要としない単一画面の Web UI を追加する。フロントエンドはフレームワークや外部 CDN に依存しない HTML、CSS、vanilla JavaScript で構成し、FastAPI と同一オリジンから配信する。これにより現在の小規模なアプリケーションに対して依存関係と運用手順を増やさず、`uvicorn app.main:app --reload` だけで API と UI の両方を利用できる。

`GET /` は UI のエントリーポイントを返し、`/static` は CSS と JavaScript を配信する。既存の `/todos`、`/docs`、`/openapi.json` は変更しない。UI は既存 API を唯一のデータソースとし、TODO の作成、一覧取得、完了状態の切り替え、削除に既存の HTTP 契約をそのまま利用する。

デザインはモバイルファーストとし、ニュートラルな背景、明確なアクセントカラー、余白、角丸、控えめな影で情報階層を表現する。色、寸法、タイポグラフィ、フォーカスリングは CSS カスタムプロパティに集約する。320px 程度の画面でも横スクロールを発生させず、広い画面ではコンテンツに最大幅を設ける。操作状態は色だけでなく文言、装飾、支援技術向け属性でも伝える。

採用する技術と判断は次のとおりとする。

- UI: セマンティック HTML5、CSS、ES Modules を使わない単一の vanilla JavaScript。小規模な1画面のため、フロントエンドフレームワークや Node.js ツールチェーンは導入しない。
- 配信: FastAPI の `FileResponse` で `/` の HTML を返し、`StaticFiles` を `/static` にマウントする。
- 通信: ブラウザ標準の `fetch` を使い、相対 URL で同一オリジンの `/todos` API を呼び出す。
- 状態管理: TODO 配列、選択中フィルター、取得中状態、項目ごとの処理中 ID を JavaScript のモジュール内状態として保持し、状態変更後に一方向に再描画する。
- セキュリティ: TODO タイトルを文字列連結した HTML として挿入せず、`textContent` または DOM API で描画し、保存値による DOM XSS を防ぐ。

## Directory Structure
```text
sample-project-for-learn-20260619/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI、GET /、/static、既存ルーターの登録
│   ├── routes.py            # 既存 /todos CRUD API（変更なし）
│   ├── schemas.py           # 既存 API スキーマ（変更なし）
│   ├── store.py             # 既存インメモリストア（変更なし）
│   └── static/
│       ├── index.html       # UI の構造、フォーム、状態・通知領域
│       ├── styles.css       # デザイントークン、レスポンシブ表示、状態表現
│       └── app.js           # API 通信、状態管理、描画、操作イベント
├── tests/
│   ├── conftest.py          # 既存 TestClient fixture
│   ├── test_todos.py        # 既存 CRUD 回帰テスト
│   └── test_ui.py           # HTML と静的アセットの配信テスト
├── architecture.md
├── plan.md
├── pyproject.toml
└── README.md                # UI の起動 URL、操作方法、確認手順
```

実装対象ファイルは次のとおりとする。

| File | Change |
| --- | --- |
| `app/main.py` | `GET /` の `FileResponse` と `/static` の `StaticFiles` を登録する |
| `app/static/index.html` | アプリシェル、作成フォーム、件数、フィルター、一覧、空状態、通知領域を新規作成する |
| `app/static/styles.css` | モバイルファーストのレイアウト、デザイントークン、各操作状態、フォーカス、縮小モーション対応を新規作成する |
| `app/static/app.js` | CRUD 通信、クライアント状態、フィルター、検証、ローディングとエラー処理を新規作成する |
| `tests/test_ui.py` | ルート HTML と CSS・JavaScript の配信、Content-Type、既存ドキュメントとの共存を検証する |
| `README.md` | UI URL、基本操作、ブラウザでの確認項目、インメモリ制約を追記する |

`app/routes.py`、`app/schemas.py`、`app/store.py` の API 実装は変更対象にしない。UI の都合で API 契約を広げず、既存挙動を回帰テストで保護する。

## Components
**Application and static delivery (`app/main.py`)**

`FastAPI` インスタンスと既存 TODO ルーターを維持しながら、アプリディレクトリからの絶対パスで `app/static` を解決する。カレントディレクトリに依存しないよう `pathlib.Path(__file__)` を基準にする。`GET /` は `index.html` を `FileResponse` で返し、`/static` は `StaticFiles` にマウントする。ルートを catch-all にせず、API、Swagger UI、OpenAPI のパス解決へ影響を与えない。

**Document shell (`app/static/index.html`)**

1画面を次の領域で構成する。

- ヘッダー: アプリ名と簡潔な用途説明。
- 作成フォーム: 明示的な `label`、最大長 200 のタイトル入力、送信ボタン、入力エラー領域。
- サマリー: 総件数と未完了件数を文言付きで表示する。
- フィルター: 「すべて」「未完了」「完了」をボタン群として提供し、選択状態を `aria-pressed` で示す。
- TODO リスト: チェックボックス、タイトル、削除ボタンを各項目に持たせる。削除ボタンには対象タイトルを含むアクセシブルネームを付ける。
- 状態領域: 初回ローディング、全体の空状態、フィルター結果なしを区別する。
- 通知領域: 成功・失敗メッセージを `aria-live` で通知する。視覚表示と読み上げの両方に利用する。

初期 HTML は JavaScript 実行前でも画面の目的が伝わる構造とする。外部フォントやアイコンは必須にせず、削除アイコンを使う場合にも可視テキストまたは `aria-label` を付ける。

**Presentation (`app/static/styles.css`)**

CSS カスタムプロパティに背景、サーフェス、文字、アクセント、危険色、境界線、影、角丸、余白、フォーカスリングを定義する。レイアウトは狭い画面を既定とし、フォームやフィルターを折り返し可能にする。メディアクエリではコンテンツ最大幅や余白だけを段階的に広げる。

完了済み TODO はチェック状態と取り消し線・補助文言で示し、処理中項目は操作を無効化して `aria-busy` と視覚的な進行表示を付ける。`:focus-visible` で高コントラストのリングを表示し、操作対象は少なくとも約 44px の高さを確保する。`prefers-reduced-motion: reduce` ではトランジションとアニメーションを無効化する。

**Client controller (`app/static/app.js`)**

責務をファイル内の小さな関数に分離する。

- API 関数: `listTodos`、`createTodo`、`updateTodo`、`deleteTodo` が `fetch` と JSON/204 応答を扱う。
- エラー正規化: 非 2xx 応答を例外へ変換し、422 の検証詳細、404、通信失敗を利用者向けの短いメッセージにする。
- 状態: `todos`、`filter`、`isLoading`、`isCreating`、`pendingIds` を保持する。
- 描画: フィルター済みリスト、件数、空状態、ボタン状態、`aria-busy` を状態から導出する。
- イベント: フォーム送信、フィルター選択、完了チェック、削除を処理する。リスト操作はイベント委譲を利用する。

タイトルは送信前に `trim()` し、空文字と 200 文字超過をクライアント側で拒否する。ただし API の 422 を最終的な検証結果として扱う。完了切り替えでは現在のタイトルと反転後の `completed` を `PUT` する。更新結果を受信するまで表示上の完了状態を確定せず、失敗時にサーバーと UI が不整合になる楽観的更新は行わない。作成中はフォーム、更新・削除中は該当項目だけを無効化し、無関係な項目の閲覧を妨げない。

通知は最後の操作結果を表示し、同じ文言を続けて通知する場合も支援技術が変化を認識できるよう更新手順を統一する。DOM ノードへの参照は初期化時に検証し、`DOMContentLoaded` 後に初回取得を開始する。

## Data Flow
初回表示の流れは次のとおりとする。

1. ブラウザが `GET /` を要求し、FastAPI が `index.html` を返す。
2. ブラウザが `/static/styles.css` と `/static/app.js` を同一オリジンから取得する。
3. JavaScript が一覧領域を `aria-busy=true` にし、ローディング状態を表示して `GET /todos` を呼ぶ。
4. 成功時は応答を `todos` に格納し、選択中フィルターに基づいて一覧、総件数、未完了件数、空状態を再描画する。
5. 失敗時は既存状態を勝手に変更せず、再試行可能なエラー通知を表示して処理中状態を解除する。

ユーザー操作の流れは次のとおりとする。

1. 作成では入力を検証後、`POST /todos` に `{title}` を送る。201 応答の TODO を状態へ追加し、入力をクリアして件数と一覧を再描画する。
2. 完了切り替えでは対象を処理中にし、`PUT /todos/{id}` に現在の `title` と反転した `completed` を送る。200 応答で対象を置換し、失敗時は元の状態を維持する。
3. 削除では対象を処理中にし、`DELETE /todos/{id}` を送る。204 応答後にだけ状態から除去する。
4. フィルター変更は API を呼ばず、保持中の `todos` から表示対象を導出する。CRUD 成功後は現在のフィルターを維持したまま再描画する。
5. 各リクエストは `finally` 相当の経路で処理中状態を必ず解除し、二重送信を防ぎつつ失敗後の再操作を可能にする。

API 応答を正として状態を更新するため、ページ再読み込み後にもインメモリストアの現状と一致する。サーバー再起動でデータが消える点と複数ワーカー非対応は既存ストアの制約として維持し、README に明記する。

## Test Strategy
自動テストは pytest と FastAPI `TestClient` を使い、既存 API 回帰テストと UI 配信テストを分ける。JavaScript のブラウザ実行環境や新しいテスト依存は導入せず、動的な操作性は手動確認で補完する。

`tests/test_ui.py` では次を検証する。

- `GET /` が 200 と `text/html` を返し、アプリ名、作成フォーム、TODO リスト領域、CSS・JavaScript参照を含む。
- `GET /static/styles.css` が 200 と CSS の Content-Type を返す。
- `GET /static/app.js` が 200 と JavaScript の Content-Type を返す。
- `/docs` と `/openapi.json` が引き続き利用でき、`/todos` の OpenAPI パスが維持される。
- 存在しない静的アセットが 404 となり、API ルートへフォールスルーしない。

既存 `tests/test_todos.py` をすべて実行し、作成・一覧・更新・削除、422、404 の契約が UI 配信追加後も変わっていないことを確認する。テストは外部ネットワーク、実サーバー、ブラウザを必要とせず `pytest` で完結させる。

手動確認では次を対象にする。

- TODO の作成、完了・未完了の往復、削除、ページ再読み込み後の一致。
- 全件・未完了・完了フィルターと、各操作直後の件数更新。
- 初回ローディング、全体の空状態、フィルター結果なし、入力エラー、422・404・通信エラーの識別。
- 320px、768px、デスクトップ幅での折り返しと横スクロールの有無。
- Tab、Shift+Tab、Space、Enter のみでの全操作と、フォーカス位置の視認性。
- スクリーンリーダー向けラベル、`aria-live`、`aria-busy`、フィルター選択状態の確認。
- OS の縮小モーション設定時に不要な動きが抑制されること。
