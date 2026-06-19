# Review
## Summary
モダンな TODO UI、既存 API を利用した作成・完了切り替え・削除・絞り込み、レスポンシブ表示、基本的なアクセシビリティ対応は実装されています。既存 API と静的配信を対象とした pytest は、レビュー時の再実行でも 13 件すべて成功しました。

ただし、配布用 wheel に UI の静的ファイルが含まれず、通常インストールした環境ではアプリを起動できません。また、初回一覧取得の失敗後にエラー状態が保持されず、データが空であるかのように表示されます。

## Issues
1. **High: wheel から `app/static/` が欠落します。** `app/main.py:10` は import 時に `StaticFiles(directory=STATIC_DIR)` を初期化しますが、`pyproject.toml` に package data の設定がありません。レビュー時に `python -m pip wheel . --no-deps --no-build-isolation` で生成物を確認したところ、`app/static/index.html`、`styles.css`、`app.js` はいずれも wheel に含まれていませんでした。したがって wheel や非 editable install からは静的ディレクトリ不在により `app.main` の import が失敗します。現在の `tests/test_ui.py` はソースツリーを直接参照するため、この不具合を検出できません。

2. **Medium: 初回取得エラーが正常な空状態として表示されます。** `app/static/app.js:183-190` は `GET /todos` の失敗時にも `loading` を解除するだけで失敗状態を保持せず、`render()` は `app/static/app.js:95-97` で「TODOはまだありません」と表示します。エラー通知も 3.5 秒で消えるため、その後は利用者が「取得失敗」と「TODOが0件」を区別できず、画面内に再試行手段もありません。これは plan の「通信エラーが明確に伝わる」要件および architecture の「再試行可能なエラー通知」と一致しません。

## Required Fixes
- `pyproject.toml` の setuptools package-data 設定などを使い、`app/static/*.html`、`app/static/*.css`、`app/static/*.js` を wheel に同梱してください。
- wheel をビルドして内容を検査するか、隔離環境へインストールして `GET /` と静的アセットの応答を確認する回帰テストを追加してください。
- 初回取得エラーを状態として保持し、空状態とは別の持続的なエラー表示と再試行操作を一覧領域に提供してください。
- 修正後に pytest 全件と、初回取得失敗からの再試行を含むブラウザ操作を確認してください。

## Decision
Decision: request_changes
