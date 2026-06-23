import html
from typing import Any

MCP_TOOLS = [
    {
        "name": "list_tables_tool",
        "description": "Lista las tablas disponibles en un esquema de SQL Server.",
    },
    {
        "name": "describe_table_tool",
        "description": "Describe columnas, tipos y claves primarias de una tabla.",
    },
    {
        "name": "run_query_tool",
        "description": "Ejecuta consultas de solo lectura (SELECT / WITH). Máximo 100 filas.",
    },
]


def _esc(value: Any) -> str:
    return html.escape(str(value))


def render_dashboard(
    connection: dict[str, Any],
    tables: list[dict[str, str]],
    tables_error: str | None,
    base_url: str,
) -> str:
    connected = connection["connected"]
    status_class = "status-ok" if connected else "status-error"
    status_label = "Conectado" if connected else "Sin conexión"
    status_icon = "●" if connected else "●"

    if tables_error:
        tables_content = f'<p class="muted error">{_esc(tables_error)}</p>'
    elif not tables:
        tables_content = '<p class="muted">No se encontraron tablas en el esquema <code>dbo</code>.</p>'
    else:
        rows = "".join(
            f"<tr><td>{_esc(t.get('TABLE_NAME', ''))}</td>"
            f"<td><span class='badge'>{_esc(t.get('TABLE_TYPE', ''))}</span></td></tr>"
            for t in tables
        )
        tables_content = f"""
        <table>
            <thead><tr><th>Tabla</th><th>Tipo</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <p class="muted count">{len(tables)} tabla(s) en <code>dbo</code></p>
        """

    tool_cards = "".join(
        f"""
        <div class="tool-card">
            <code>{_esc(tool['name'])}</code>
            <p>{_esc(tool['description'])}</p>
        </div>
        """
        for tool in MCP_TOOLS
    )

    sql_version = connection.get("sql_version")
    version_block = (
        f'<p class="detail"><span>Versión</span><strong>{_esc(sql_version)}</strong></p>'
        if sql_version
        else ""
    )
    error_block = (
        f'<p class="error-box">{_esc(connection["error"])}</p>' if connection.get("error") else ""
    )

    mcp_url = f"{base_url.rstrip('/')}/mcp-server/mcp"
    docs_url = f"{base_url.rstrip('/')}/docs"
    health_url = f"{base_url.rstrip('/')}/health"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP SQL Server — Dashboard</title>
    <style>
        :root {{
            --bg: #0f1419;
            --surface: #1a2332;
            --surface2: #243044;
            --border: #2d3a4f;
            --text: #e7ecf3;
            --muted: #8b9cb3;
            --accent: #3b82f6;
            --ok: #22c55e;
            --error: #ef4444;
            --code-bg: #111827;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a5f 0%, #0f1419 100%);
            border-bottom: 1px solid var(--border);
            padding: 2rem 1.5rem;
        }}
        .header-inner {{ max-width: 1100px; margin: 0 auto; }}
        .header h1 {{ font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }}
        .header p {{ color: var(--muted); font-size: 0.95rem; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 1.5rem; }}
        .grid {{ display: grid; gap: 1.25rem; }}
        @media (min-width: 768px) {{
            .grid-2 {{ grid-template-columns: 1fr 1fr; }}
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
        }}
        .card h2 {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
            margin-bottom: 1rem;
        }}
        .status-row {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .status-ok {{
            background: rgba(34, 197, 94, 0.15);
            color: var(--ok);
        }}
        .status-error {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--error);
        }}
        .detail {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }}
        .detail:last-child {{ border-bottom: none; }}
        .detail span {{ color: var(--muted); }}
        .detail strong {{ text-align: right; word-break: break-all; }}
        .error-box {{
            margin-top: 0.75rem;
            padding: 0.75rem 1rem;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            color: #fca5a5;
            font-size: 0.85rem;
            word-break: break-word;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.6rem 0.5rem;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: var(--muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
        tr:last-child td {{ border-bottom: none; }}
        .badge {{
            display: inline-block;
            padding: 0.15rem 0.5rem;
            background: var(--surface2);
            border-radius: 4px;
            font-size: 0.75rem;
            color: var(--muted);
        }}
        .muted {{ color: var(--muted); font-size: 0.85rem; }}
        .count {{ margin-top: 0.75rem; }}
        .tool-card {{
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }}
        .tool-card:last-child {{ margin-bottom: 0; }}
        .tool-card code {{
            display: block;
            color: #93c5fd;
            font-size: 0.9rem;
            margin-bottom: 0.35rem;
        }}
        .tool-card p {{ color: var(--muted); font-size: 0.85rem; }}
        .links {{ display: flex; flex-wrap: wrap; gap: 0.75rem; }}
        .link-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.6rem 1rem;
            background: var(--accent);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: opacity 0.15s;
        }}
        .link-btn:hover {{ opacity: 0.9; }}
        .link-btn.secondary {{
            background: var(--surface2);
            border: 1px solid var(--border);
            color: var(--text);
        }}
        code {{
            background: var(--code-bg);
            padding: 0.1rem 0.35rem;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        .endpoint {{
            margin-top: 1rem;
            padding: 0.75rem 1rem;
            background: var(--code-bg);
            border-radius: 8px;
            font-family: Consolas, monospace;
            font-size: 0.8rem;
            word-break: break-all;
            color: #93c5fd;
        }}
        .footer {{
            text-align: center;
            padding: 2rem 1rem;
            color: var(--muted);
            font-size: 0.8rem;
        }}
        .playground {{ margin-top: 1.25rem; }}
        .tool-tabs {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }}
        .tool-tab {{
            padding: 0.45rem 0.85rem;
            border: 1px solid var(--border);
            background: var(--surface2);
            color: var(--text);
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
        }}
        .tool-tab.active {{ background: var(--accent); border-color: var(--accent); color: white; }}
        .tool-panel {{ display: none; }}
        .tool-panel.active {{ display: block; }}
        .form-row {{ margin-bottom: 0.75rem; }}
        .form-row label {{ display: block; color: var(--muted); font-size: 0.8rem; margin-bottom: 0.25rem; }}
        .form-row input, .form-row textarea {{
            width: 100%;
            padding: 0.6rem 0.75rem;
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-family: inherit;
            font-size: 0.9rem;
        }}
        .form-row textarea {{ min-height: 90px; font-family: Consolas, monospace; resize: vertical; }}
        .run-btn {{
            padding: 0.55rem 1rem;
            background: var(--ok);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .run-btn:hover {{ opacity: 0.9; }}
        .run-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .result-box {{
            margin-top: 1rem;
            padding: 1rem;
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-family: Consolas, monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 320px;
            overflow: auto;
            color: #d1fae5;
        }}
        .result-box.error {{ color: #fca5a5; }}
        .hint {{ color: var(--muted); font-size: 0.8rem; margin-top: 0.5rem; }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <h1>MCP SQL Server</h1>
            <p>Servidor Model Context Protocol con FastAPI y SQL Server (solo lectura)</p>
        </div>
    </header>

    <main class="container">
        <div class="grid grid-2" style="margin-bottom: 1.25rem;">
            <section class="card">
                <h2>Estado de conexión</h2>
                <div class="status-row">
                    <span class="status-badge {status_class}">{status_icon} {status_label}</span>
                </div>
                <p class="detail"><span>Servidor</span><strong>{_esc(connection['server'])}</strong></p>
                <p class="detail"><span>Base de datos</span><strong>{_esc(connection['database'])}</strong></p>
                <p class="detail"><span>Driver configurado</span><strong>{_esc(connection.get('driver_configured', connection.get('driver', '')))}</strong></p>
                <p class="detail"><span>Driver en uso</span><strong>{_esc(connection.get('driver_resolved') or '—')}</strong></p>
                <p class="detail"><span>Modo</span><strong>{'Solo lectura' if connection['readonly'] else 'Lectura/escritura'}</strong></p>
                {version_block}
                {error_block}
            </section>

            <section class="card">
                <h2>Enlaces rápidos</h2>
                <div class="links">
                    <a class="link-btn" href="{_esc(docs_url)}" target="_blank">Swagger /docs</a>
                    <a class="link-btn secondary" href="{_esc(health_url)}" target="_blank">Health check</a>
                </div>
                <p class="muted" style="margin-top: 1rem;">Endpoint MCP (Streamable HTTP):</p>
                <div class="endpoint">{_esc(mcp_url)}</div>
            </section>
        </div>

        <div class="grid grid-2">
            <section class="card">
                <h2>Tablas — esquema dbo</h2>
                {tables_content}
            </section>

            <section class="card">
                <h2>Tools MCP disponibles</h2>
                {tool_cards}
                <p class="hint">Las mismas tools están disponibles abajo en el playground y en <a href="{_esc(docs_url)}" style="color:#93c5fd">/docs</a>.</p>
            </section>
        </div>

        <section class="card playground" id="playground">
            <h2>Probar tools — interfaz gráfica</h2>
            <p class="muted" style="margin-bottom: 1rem;">Ejecuta las tools desde el navegador. MCP en Cursor usa el mismo backend.</p>

            <div class="tool-tabs">
                <button class="tool-tab active" data-panel="list">list_tables_tool</button>
                <button class="tool-tab" data-panel="describe">describe_table_tool</button>
                <button class="tool-tab" data-panel="query">run_query_tool</button>
            </div>

            <div class="tool-panel active" id="panel-list">
                <div class="form-row">
                    <label for="schema-list">Esquema</label>
                    <input id="schema-list" type="text" value="dbo">
                </div>
                <button class="run-btn" onclick="runListTables()">Ejecutar list_tables_tool</button>
            </div>

            <div class="tool-panel" id="panel-describe">
                <div class="form-row">
                    <label for="schema-desc">Esquema</label>
                    <input id="schema-desc" type="text" value="dbo">
                </div>
                <div class="form-row">
                    <label for="table-desc">Tabla</label>
                    <input id="table-desc" type="text" placeholder="Nombre de tabla">
                </div>
                <button class="run-btn" onclick="runDescribeTable()">Ejecutar describe_table_tool</button>
            </div>

            <div class="tool-panel" id="panel-query">
                <div class="form-row">
                    <label for="sql-query">SQL (solo SELECT / WITH)</label>
                    <textarea id="sql-query" placeholder="SELECT TOP 5 * FROM dbo.TuTabla"></textarea>
                </div>
                <button class="run-btn" onclick="runQuery()">Ejecutar run_query_tool</button>
            </div>

            <pre class="result-box" id="result">El resultado aparecerá aquí…</pre>
        </section>
    </main>

    <footer class="footer">
        MCP Base API v1.0.0 · <a href="#playground" style="color:#93c5fd">Playground</a> · <a href="{_esc(docs_url)}" style="color:#93c5fd">Swagger</a>
    </footer>

    <script>
        document.querySelectorAll('.tool-tab').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.tool-tab').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
            }});
        }});

        const resultEl = document.getElementById('result');

        function showResult(data, isError = false) {{
            resultEl.classList.toggle('error', isError);
            resultEl.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
        }}

        async function runListTables() {{
            const schema = document.getElementById('schema-list').value || 'dbo';
            showResult('Ejecutando…');
            try {{
                const r = await fetch('/api/tables?schema=' + encodeURIComponent(schema));
                const data = await r.json();
                showResult(data, !r.ok);
            }} catch (e) {{ showResult('Error: ' + e.message, true); }}
        }}

        async function runDescribeTable() {{
            const schema = document.getElementById('schema-desc').value || 'dbo';
            const table = document.getElementById('table-desc').value.trim();
            if (!table) {{ showResult('Indica el nombre de la tabla.', true); return; }}
            showResult('Ejecutando…');
            try {{
                const r = await fetch('/api/tables/' + encodeURIComponent(schema) + '/' + encodeURIComponent(table));
                const data = await r.json();
                showResult(data, !r.ok);
            }} catch (e) {{ showResult('Error: ' + e.message, true); }}
        }}

        async function runQuery() {{
            const sql = document.getElementById('sql-query').value.trim();
            if (!sql) {{ showResult('Escribe una consulta SQL.', true); return; }}
            showResult('Ejecutando…');
            try {{
                const r = await fetch('/api/query', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ sql }})
                }});
                const data = await r.json();
                showResult(data, !r.ok);
            }} catch (e) {{ showResult('Error: ' + e.message, true); }}
        }}
    </script>
</body>
</html>"""
