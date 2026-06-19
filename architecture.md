# Architecture
## Overview
単一プロセスで動作する小規模な FastAPI アプリケーションとして実装する。HTTP 層、Pydantic スキーマ、インメモリストアを分離し、ルーターは FastAPI の依存性注入を通じてストアを利用する。これにより、現時点では簡潔な構成を保ちつつ、将来データベースへ移行する場合もストレージ実装の差し替え範囲を限定する。

- Python 3.11 以降を対象とする。
- Web フレームワークは FastAPI、ASGI サーバーは Uvicorn を使用する。
- Pydantic v2 のモデルで入力検証とレスポンス定義を行う。
- 永続化は `dict[int, Todo]` を内部に持つ `TodoStore` とし、プロセス内で単調増加する整数 ID を採番する。
- 依存関係とツール設定は `pyproject.toml` に集約し、アプリ依存と pytest を同じ手順で導入できるようにする。
- API の基底パスは `/todos` とし、更新は全フィールドを受け取る `PUT` とする。

## Directory Structure
```text
sample-project/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI インスタンス生成、ルーター登録
│   ├── routes.py        # /todos CRUD エンドポイント
│   ├── schemas.py       # TodoCreate、TodoUpdate、TodoResponse
│   └── store.py         # TodoStore と依存性注入用プロバイダー
├── tests/
│   ├── conftest.py      # TestClient と独立ストアの fixture
│   └── test_todos.py    # CRUD、検証エラー、404 の API テスト
├── architecture.md
├── plan.md
├── pyproject.toml
└── README.md
```

## Components
**Application (`app/main.py`)**

`FastAPI` インスタンスを公開し、TODO ルーターを登録する。起動点は `uvicorn app.main:app` とする。FastAPI 標準の `/docs` と `/openapi.json` を有効のまま利用する。

**Schemas (`app/schemas.py`)**

- `TodoCreate`: `title: str` と省略可能な `completed: bool = False` を受け取る。
- `TodoUpdate`: PUT の全体更新として `title: str` と `completed: bool` を必須にする。
- `TodoResponse`: `id: int`、`title: str`、`completed: bool` を返す。
- `title` は前後の空白を除去し、空文字を拒否する。長さには妥当な上限を設定し、違反時は FastAPI 標準の HTTP 422 を返す。

**Store (`app/store.py`)**

`TodoStore` が作成、一覧、取得、更新、削除を同期メソッドとして提供する。一覧は ID の昇順で返す。ルーターへは `get_todo_store()` を `Depends` で注入し、通常実行ではアプリプロセス内の単一インスタンスを利用する。存在判定と HTTP 例外の変換はルーター側で行い、ストアは対象がない場合に `None` を返す。

これは開発・デモ用途の実装であり、複数ワーカー、プロセス再起動後の保持、分散ロックは対象外とする。本番永続化が必要になった時点で同じ操作契約を持つ DB リポジトリへ置き換える。

**Routes (`app/routes.py`)**

| Method | Path | Success | Behavior |
| --- | --- | --- | --- |
| `POST` | `/todos` | 201 | TODO を作成して返す |
| `GET` | `/todos` | 200 | TODO の一覧を返す |
| `GET` | `/todos/{todo_id}` | 200 | 指定 TODO を返す |
| `PUT` | `/todos/{todo_id}` | 200 | 指定 TODO を全体更新して返す |
| `DELETE` | `/todos/{todo_id}` | 204 | 指定 TODO を削除し、本文は返さない |

個別取得・更新・削除で ID が存在しない場合は、共通の `404 Todo not found` を返す。レスポンスモデルを各エンドポイントに明示し、実装内部の表現が API に漏れないようにする。

**Project Metadata and Documentation**

`pyproject.toml` に FastAPI、Uvicorn、pytest、HTTPX を定義し、pytest のテスト探索設定も置く。README には仮想環境作成、インストール、起動、テスト実行、各 API の curl 例、インメモリ方式の制約を記載する。

## Data Flow
1. クライアントが JSON リクエストを TODO エンドポイントへ送信する。
2. FastAPI がパス・HTTP メソッドを解決し、Pydantic スキーマでリクエストを検証する。不正な入力はストアへ到達せず HTTP 422 になる。
3. ルーターが `Depends(get_todo_store)` から `TodoStore` を受け取る。
4. ルーターが CRUD 操作を呼び出し、対象がなければ HTTP 404 に変換する。
5. FastAPI が結果を `TodoResponse` または `list[TodoResponse]` で検証・シリアライズして返す。削除成功時のみ本文なしの HTTP 204 を返す。

ID 採番とデータ変更は `TodoStore` に閉じ込める。非同期 I/O がないためエンドポイントとストアは同期実装とし、不要な async 抽象化は導入しない。

## Test Strategy
pytest と FastAPI の `TestClient` を使い、HTTP 境界から振る舞いを検証する。`tests/conftest.py` では各テストごとに新しい `TodoStore` を生成し、`app.dependency_overrides` で注入する。テスト終了後に override を解除し、順序依存と状態漏れを防ぐ。

- 作成: 201、デフォルト値、採番、連続作成時の一意 ID。
- 一覧・個別取得: 空一覧、複数件、作成内容との一致。
- 更新: 200、全フィールド更新、更新後の取得結果。
- 削除: 204、空のレスポンス本文、削除後の 404。
- 異常系: 取得・更新・削除の未知 ID に対する 404。
- バリデーション: 空文字、空白のみ、欠落フィールド、不正な型に対する 422。

テストは外部ネットワークや実サーバーを必要とせず、`pytest` のみで完結させる。加えてアプリ import と OpenAPI 生成が成功することを確認し、ルート定義やレスポンスモデルの構成エラーも検出する。
