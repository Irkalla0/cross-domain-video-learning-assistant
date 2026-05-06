# Run Evals

## 1) 准备路径
- Skill 路径：`C:\Users\Irkalla\Documents\Codex\2026-05-06\skill-creator-skill\cross-domain-video-learning-assistant`
- Workspace（示例）：`C:\Users\Irkalla\Documents\Codex\2026-05-06\skill-creator-skill\cross-domain-video-learning-assistant-workspace\iteration-1`
- Evals：`...\cross-domain-video-learning-assistant\evals\evals.json`

## 2) 执行策略
- 每个 eval 跑两组：
  1. `with_skill`（加载本 skill）
  2. `without_skill`（不加载 skill）
- 登录受限用例（id=7/8）先检查本机会话；若失效，用户手动登录后继续。

## 3) 断言参考
- 见 `assertion-checklist.json`。
- 每个 run 产出 `grading.json` 时，建议使用字段：`text`, `passed`, `evidence`。

## 4) 聚合 benchmark（示例）
```bash
python -m scripts.aggregate_benchmark "C:\Users\Irkalla\Documents\Codex\2026-05-06\skill-creator-skill\cross-domain-video-learning-assistant-workspace\iteration-1" --skill-name "cross-domain-video-learning-assistant"
```

## 5) 生成评审页（示例）
```bash
python "C:\Users\Irkalla\.codex\skills\skill-creator\eval-viewer\generate_review.py" "C:\Users\Irkalla\Documents\Codex\2026-05-06\skill-creator-skill\cross-domain-video-learning-assistant-workspace\iteration-1" --skill-name "cross-domain-video-learning-assistant" --benchmark "C:\Users\Irkalla\Documents\Codex\2026-05-06\skill-creator-skill\cross-domain-video-learning-assistant-workspace\iteration-1\benchmark.json" --static "C:\Users\Irkalla\Documents\Codex\2026-05-06\skill-creator-skill\cross-domain-video-learning-assistant-workspace\iteration-1\review.html"
```
