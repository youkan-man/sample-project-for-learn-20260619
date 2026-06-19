# Review
## Summary
モダンな TODO UI、既存 API を利用する作成・完了切り替え・削除・絞り込み、レスポンシブ表示、基本的なアクセシビリティ対応が実装されています。既存 API と静的配信を対象とした pytest は 13 件すべて成功しています。

ただし、ビルドした wheel に UI の静的ファイルが同梱されないため、通常インストールした配布物ではアプリを起動できません。ソースツリー上および editable install でのみ動作する状態です。

## Issues
1. **High: wheel から `app/static/` が欠落します。** `app/main.py:10` は import 時に `StaticFiles(directory=STATIC_DIR)` を初期化しますが、`pyproject.toml` に package data の設定がありません。`python -m pip wheel . --no-deps --no-build-isolation` で生成した wheel を確認したところ、`app/static/index.html`、`styles.css`、`app.js` は一つも含まれていませんでした。そのため非 editable な `pip install .` や wheel 配布後の環境では、`app.main` の import が静的ディレクトリ不在で失敗します。現在の `tests/test_ui.py` はソースツリーを直接使うため、この欠落を検出できません。

## Required Fixes
- `pyproject.toml` の setuptools package-data 設定などを使い、`app/static/*.html`、`app/static/*.css`、`app/static/*.js` を wheel に同梱してください。
- wheel をビルドして展開または隔離環境へインストールし、静的ファイルの存在と `GET /`、`GET /static/styles.css`、`GET /static/app.js` の成功を確認する回帰テストまたは検証手順を追加してください。
- 修正後に既存の pytest 全件を再実行してください。

## Decision
Decision: request_changes
