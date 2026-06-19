# TODO API

FastAPI で実装した、インメモリ方式のシンプルな TODO CRUD API です。

## 必要環境

- Python 3.11 以上

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 起動

```bash
uvicorn app.main:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開くと TODO 管理画面を利用できます。
追加のフロントエンドビルドは不要です。Swagger UI は
`http://127.0.0.1:8000/docs` で確認できます。

## Web UI

- 入力欄にタイトルを入れて「追加」を押すと TODO を作成します。
- チェックボックスで完了・未完了を切り替え、右端の削除ボタンで削除します。
- 「すべて」「未完了」「完了」で一覧を絞り込めます。
- 一覧上部には総件数と未完了件数が表示されます。

狭い画面での折り返し、キーボードでの Tab・Enter・Space 操作、空状態や
入力エラーを確認する場合は、ブラウザの開発者ツールで幅を 320px 程度まで
縮めて操作してください。

## テスト

```bash
pytest
```

## API

| Method | Path | 説明 |
| --- | --- | --- |
| `POST` | `/todos` | TODO を作成 |
| `GET` | `/todos` | TODO を一覧取得 |
| `GET` | `/todos/{todo_id}` | TODO を個別取得 |
| `PUT` | `/todos/{todo_id}` | TODO を全体更新 |
| `DELETE` | `/todos/{todo_id}` | TODO を削除 |

### 作成

```bash
curl -i -X POST http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"READMEを書く"}'
```

```json
{"id":1,"title":"READMEを書く","completed":false}
```

### 一覧・個別取得

```bash
curl http://127.0.0.1:8000/todos
curl http://127.0.0.1:8000/todos/1
```

### 更新

`PUT` では `title` と `completed` の両方が必須です。

```bash
curl -X PUT http://127.0.0.1:8000/todos/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"READMEを書く","completed":true}'
```

### 削除

```bash
curl -i -X DELETE http://127.0.0.1:8000/todos/1
```

作成時は HTTP 201、削除時は HTTP 204、存在しない ID は HTTP 404、
不正な入力は HTTP 422 を返します。タイトルは前後の空白を除去し、1 文字以上
200 文字以下を許可します。

## 制約

データはプロセス内のメモリだけに保持されます。サーバーの再起動で消失し、複数
ワーカー間では共有されないため、開発・デモ用途を想定しています。
