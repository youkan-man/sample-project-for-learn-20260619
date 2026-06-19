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

API は `http://127.0.0.1:8000`、Swagger UI は
`http://127.0.0.1:8000/docs` で確認できます。

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
