# -*- coding: utf-8 -*-
"""Step 5: 產出 HTML 日報。彙整前四步中間產物。"""
import argparse
import json
from pathlib import Path


def build_html(s1, s2, s3, s4, run_id):
    top3_lookup = {a["id"]: a for a in s3["articles"]}
    cards = ""
    for i, t in enumerate(s3["top3"], 1):
        a = top3_lookup[t["id"]]
        cc = ""
        if a.get("cross_cloud"):
            rows = "".join(
                f"<tr><td>{r['能力']}</td><td>{r['aws']}</td><td>{r['gcp']}</td><td>{r['azure']}</td></tr>"
                for r in a["cross_cloud"])
            cc = f"<details><summary>跨雲對應</summary><table><tr><th>能力</th><th>AWS</th><th>GCP</th><th>Azure</th></tr>{rows}</table></details>"
        if t.get("matched_cases"):
            case_rows = "".join(
                f"<li><b>{m['customer']}</b> "
                f"<span class='relv'>相關性 {m['relevance_to_cathay']}/5</span> "
                f"<span class='tags'>共通：{'、'.join(m['overlap_tags'])}</span></li>"
                for m in t["matched_cases"][:3])
            cases_html = f'<div class="cases"><b>📚 引用案例（{len(t["matched_cases"])} 筆）</b><ul>{case_rows}</ul></div>'
        else:
            cases_html = '<div class="cases no-case">⚠ 無 enterprise 案例可對照</div>'
        flagged = any(f["id"] == t["id"] for f in s4["hard_rule_flags"])
        badge = '<span class="flag">⚠ 驗證者標記</span>' if flagged else ""
        cards += f"""
      <article class="pick">
        <div class="pick-no">{i}</div>
        <div class="pick-body">
          <h3>{a['title']} {badge}</h3>
          <p class="meta">{a['source']} · {a['date']} · L2 <b>{t['l2_score']}</b></p>
          <p>{a['summary']}</p>
          <p class="reason">{t['reason']}</p>
          {cases_html}{cc}
        </div>
      </article>"""

    total_saved = sum(1 for _ in s1["dropped"]) + s2.get("input_count", 0) - s2["kept_count"]
    dis_html = "".join(f"<li><b>{d['id']}</b>：{d['note']}</li>" for d in s4["disagreements"]) or "<li>無分歧</li>"
    drop_html = "".join(f"<li><b>{d['id']}</b> {d['title']}<br><span class='why'>{d['reason']}</span></li>" for d in s1["dropped"])

    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>雲端技術情報日報 · {run_id}</title>
<style>
:root{{--paper:#F4F7F6;--ink:#17262B;--petrol:#0E5A6D;--petrol-dk:#093B48;--signal:#E8590C;--mute:#6C7E84;--line:#D5DFDE;--card:#fff;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Microsoft JhengHei",sans-serif;line-height:1.7;padding:0 0 4rem;}}
header{{background:var(--petrol-dk);color:#E9F2F1;padding:2rem 1.5rem;}}
header .eb{{font-family:ui-monospace,Menlo,monospace;font-size:.72rem;letter-spacing:.28em;color:#7FB6C2;text-transform:uppercase;}}
header h1{{font-size:1.4rem;margin:.4rem 0 .2rem;}}
header p{{color:#A8C8CE;font-size:.85rem;}}
main{{max-width:820px;margin:0 auto;padding:0 1.2rem;}}
section{{margin-top:2rem;}}
h2{{font-size:1rem;color:var(--petrol);border-left:4px solid var(--petrol);padding-left:.6rem;margin-bottom:1rem;}}
.pick{{background:var(--card);border:1px solid var(--line);border-radius:6px;display:flex;gap:1rem;padding:1.1rem 1.2rem;margin-bottom:1rem;}}
.pick-no{{font-family:ui-monospace,Menlo,monospace;font-size:1.6rem;font-weight:700;color:var(--petrol);min-width:2rem;}}
.pick h3{{font-size:1rem;}}
.pick .meta{{font-size:.78rem;color:var(--mute);margin:.15rem 0 .45rem;}}
.pick p{{font-size:.88rem;}}
.pick .reason{{margin-top:.4rem;color:var(--petrol-dk);font-size:.85rem;background:#EDF4F3;border-radius:3px;padding:.35rem .6rem;}}
.cases{{margin-top:.5rem;font-size:.82rem;background:#FFF9F0;border-left:3px solid var(--signal);border-radius:3px;padding:.4rem .7rem;}}
.cases ul{{padding-left:1.1rem;margin-top:.2rem;}}
.cases .relv{{color:var(--signal);font-family:ui-monospace,Menlo,monospace;font-size:.72rem;}}
.cases .tags{{color:var(--mute);font-size:.72rem;}}
.cases.no-case{{background:#FBECEC;border-left-color:#C0392B;color:#8B2C1F;}}
.flag{{color:var(--signal);font-size:.72rem;font-weight:700;}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:1rem 1.2rem;font-size:.87rem;}}
.panel ul{{padding-left:1.2rem;margin-top:.4rem;}}
.mono{{font-family:ui-monospace,Menlo,monospace;}}
.verdict{{display:inline-block;padding:.2rem .7rem;border-radius:3px;font-weight:700;font-size:.85rem;}}
.pass{{background:#DDEEE7;color:#1B6B4A;}}
.review{{background:#FBE4D5;color:var(--signal);}}
.why{{color:var(--mute);font-size:.8rem;}}
details{{margin-top:.5rem;font-size:.82rem;}}
summary{{cursor:pointer;color:var(--petrol);}}
table{{border-collapse:collapse;margin-top:.4rem;width:100%;font-size:.78rem;}}
th,td{{border:1px solid var(--line);padding:.3rem .5rem;text-align:left;}}
th{{background:#EDF4F3;}}
footer{{text-align:center;color:var(--mute);font-size:.75rem;margin-top:3rem;font-family:ui-monospace,Menlo,monospace;}}
</style></head><body>
<header>
  <div class="eb">Daily Tech Intel · v3 · Skills + API</div>
  <h1>雲端技術情報日報</h1>
  <p>執行 ID：{run_id} · 資料來源：{s1['source_mode']} · 評估：{s3.get('mode','?')}</p>
</header>
<main>
  <section><h2>今日 AI 選 3</h2>{cards}</section>
  <section><h2>獨立驗證（建造者 ≠ 驗證者）</h2>
    <div class="panel">
      <p>驗證者模式：{s4['mode']}</p>
      <p style="margin-top:.4rem">一致率：<b>{int(s4['agreement_rate']*100)}%</b>　判定：
        <span class="verdict {'pass' if s4['verdict']=='通過' else 'review'}">{s4['verdict']}</span></p>
      <p style="margin-top:.4rem"><b>建造者 Top-3：</b><span class="mono">{', '.join(s4['builder_top3'])}</span></p>
      <p><b>驗證者 Top-3：</b><span class="mono">{', '.join(s4['validator_top3'])}</span></p>
      <p style="margin-top:.4rem"><b>分歧：</b></p><ul>{dis_html}</ul>
    </div>
  </section>
  <section><h2>案例庫</h2>
    <div class="panel">
      <p>本次評估載入 <b>{s3['case_studies_loaded']}</b> 個 enterprise 案例。</p>
      <p style="margin-top:.4rem">📚 <span class="mono">{', '.join(s3['case_studies_ids'])}</span></p>
    </div>
  </section>
  <section><h2>L0 過濾紀錄</h2>
    <div class="panel"><ul>{drop_html}</ul></div>
  </section>
</main>
<footer>pipeline v3 · api.anthropic.com · builder≠validator enforced</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="含 s1-s4 JSON 的目錄")
    ap.add_argument("--output", required=True)
    ap.add_argument("--run-id", default="manual")
    args = ap.parse_args()

    d = Path(args.run_dir)
    def load(name): return json.load(open(d/name, encoding="utf-8"))
    html = build_html(load("s1_scan.json"), load("s2_compare.json"),
                      load("s3_evaluate.json"), load("s4_validate.json"),
                      args.run_id)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[S5] 報告寫到 {args.output}")


if __name__ == "__main__":
    main()
