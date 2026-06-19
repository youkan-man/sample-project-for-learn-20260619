(() => {
  "use strict";

  const state = { todos: [], filter: "all", loading: true, creating: false, pending: new Set() };
  const form = document.querySelector("#todo-form");
  const input = document.querySelector("#todo-title");
  const createButton = document.querySelector("#create-button");
  const list = document.querySelector("#todo-list");
  const region = document.querySelector("#list-region");
  const status = document.querySelector("#status");
  const summary = document.querySelector("#summary");
  const error = document.querySelector("#input-error");
  const notification = document.querySelector("#notification");
  const filterButtons = [...document.querySelectorAll("[data-filter]")];
  let notificationTimer;

  function showNotification(message, isError = false) {
    clearTimeout(notificationTimer);
    notification.className = `toast ${isError ? "error " : ""}visible`;
    notification.textContent = message;
    notificationTimer = setTimeout(() => notification.className = "toast", 3500);
  }

  async function request(url, options = {}) {
    let response;
    try {
      response = await fetch(url, options);
    } catch (_error) {
      throw new Error("サーバーに接続できません。時間をおいて再度お試しください。");
    }
    if (!response.ok) {
      let detail;
      try { detail = (await response.json()).detail; } catch (_error) { detail = null; }
      if (response.status === 404) throw new Error("対象のTODOが見つかりません。再読み込みしてください。");
      if (response.status === 422) throw new Error("入力内容を確認してください。");
      throw new Error(typeof detail === "string" ? detail : "操作を完了できませんでした。");
    }
    return response.status === 204 ? null : response.json();
  }

  function visibleTodos() {
    if (state.filter === "active") return state.todos.filter((todo) => !todo.completed);
    if (state.filter === "completed") return state.todos.filter((todo) => todo.completed);
    return state.todos;
  }

  function renderTodo(todo) {
    const item = document.createElement("li");
    item.className = `todo-item${todo.completed ? " completed" : ""}`;
    item.dataset.id = String(todo.id);
    item.setAttribute("aria-busy", String(state.pending.has(todo.id)));

    const main = document.createElement("div");
    main.className = "todo-main";
    const checkbox = document.createElement("input");
    checkbox.className = "todo-checkbox";
    checkbox.type = "checkbox";
    checkbox.checked = todo.completed;
    checkbox.disabled = state.pending.has(todo.id);
    checkbox.setAttribute("aria-label", `「${todo.title}」を${todo.completed ? "未完了" : "完了"}にする`);
    const text = document.createElement("div");
    const title = document.createElement("span");
    title.className = "todo-title";
    title.textContent = todo.title;
    const stateLabel = document.createElement("span");
    stateLabel.className = "state-label";
    stateLabel.textContent = todo.completed ? "完了済み" : "未完了";
    text.append(title, stateLabel);
    main.append(checkbox, text);

    const remove = document.createElement("button");
    remove.className = "delete-button";
    remove.type = "button";
    remove.dataset.action = "delete";
    remove.disabled = state.pending.has(todo.id);
    remove.setAttribute("aria-label", `「${todo.title}」を削除`);
    remove.textContent = "×";
    item.append(main, remove);
    return item;
  }

  function render() {
    const remaining = state.todos.filter((todo) => !todo.completed).length;
    summary.textContent = `${state.todos.length}件 / 未完了 ${remaining}件`;
    region.setAttribute("aria-busy", String(state.loading));
    createButton.disabled = state.creating;
    input.disabled = state.creating;
    createButton.lastChild.textContent = state.creating ? " 追加中..." : " 追加";
    filterButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.filter === state.filter)));

    list.replaceChildren(...visibleTodos().map(renderTodo));
    if (state.loading) {
      status.textContent = "読み込み中...";
      status.hidden = false;
    } else if (state.todos.length === 0) {
      status.textContent = "TODOはまだありません。最初のひとつを追加しましょう。";
      status.hidden = false;
    } else if (visibleTodos().length === 0) {
      status.textContent = "この条件に一致するTODOはありません。";
      status.hidden = false;
    } else {
      status.hidden = true;
    }
  }

  function validateTitle() {
    const title = input.value.trim();
    const message = !title ? "TODOを入力してください。" : title.length > 200 ? "TODOは200文字以内で入力してください。" : "";
    error.textContent = message;
    input.setAttribute("aria-invalid", String(Boolean(message)));
    return message ? null : title;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const title = validateTitle();
    if (!title) return input.focus();
    state.creating = true;
    render();
    try {
      const todo = await request("/todos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }) });
      state.todos.push(todo);
      input.value = "";
      error.textContent = "";
      showNotification("TODOを追加しました。");
    } catch (requestError) {
      showNotification(requestError.message, true);
    } finally {
      state.creating = false;
      render();
      input.focus();
    }
  });

  input.addEventListener("input", () => {
    if (error.textContent) validateTitle();
  });

  filterButtons.forEach((button) => button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    render();
  }));

  list.addEventListener("change", async (event) => {
    if (!event.target.matches(".todo-checkbox")) return;
    const item = event.target.closest("[data-id]");
    const id = Number(item.dataset.id);
    const todo = state.todos.find((entry) => entry.id === id);
    state.pending.add(id);
    render();
    try {
      const updated = await request(`/todos/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: todo.title, completed: !todo.completed }) });
      state.todos = state.todos.map((entry) => entry.id === id ? updated : entry);
      showNotification(updated.completed ? "TODOを完了にしました。" : "TODOを未完了に戻しました。");
    } catch (requestError) {
      showNotification(requestError.message, true);
    } finally {
      state.pending.delete(id);
      render();
    }
  });

  list.addEventListener("click", async (event) => {
    const button = event.target.closest('[data-action="delete"]');
    if (!button) return;
    const id = Number(button.closest("[data-id]").dataset.id);
    state.pending.add(id);
    render();
    try {
      await request(`/todos/${id}`, { method: "DELETE" });
      state.todos = state.todos.filter((todo) => todo.id !== id);
      showNotification("TODOを削除しました。");
    } catch (requestError) {
      showNotification(requestError.message, true);
    } finally {
      state.pending.delete(id);
      render();
    }
  });

  document.querySelector("#today").textContent = new Intl.DateTimeFormat("ja-JP", { month: "long", day: "numeric", weekday: "short" }).format(new Date());

  async function loadTodos() {
    try {
      state.todos = await request("/todos");
    } catch (requestError) {
      showNotification(requestError.message, true);
    } finally {
      state.loading = false;
      render();
    }
  }

  render();
  loadTodos();
})();
