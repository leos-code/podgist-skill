[english](./READM_EN.md)

# podgist-skill

本地 Codex 插件，用于将播客单集转换为保存的本地文件：

- 通过 Apple iTunes Search API 搜索单集
- 单集下载与 ffmpeg 格式标准化
- 使用 `faster-whisper` 本地转录
- 生成中文分析文档与话题时间戳
- 基于已保存文件的有依据问答

## 目录结构

- `.codex-plugin/plugin.json`：插件清单
- `skills/`：六个专注的 Codex 技能加一个编排器
- `scripts/`：可复用的 Python 流程
- `references/`：文件与提示词约定
- `evals/`：手动评估提示词
- `artifacts/`：由脚本创建的单集输出

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

必需的运行依赖：

- `ffmpeg`（位于 `PATH` 中）
- Python 3.10+
- `faster-whisper`

可选：

- `OPENAI_API_KEY`：让 `analyze_episode.py` 和 `qa_transcript.py` 使用 Responses API
  以获得更丰富的自然语言输出。未设置时，两个脚本将回退到本地启发式逻辑。

## 常用流程

搜索：

```bash
python3 scripts/search_episodes.py --query "lex fridman openai" --limit 5 --output /tmp/candidates.json
```

下载并标准化：

```bash
python3 scripts/download_episode.py --candidate-file /tmp/candidates.json --index 0
```

转录：

```bash
python3 scripts/transcribe_episode.py --artifact-dir artifacts/<slug>-<trackId>
```

分析：

```bash
python3 scripts/analyze_episode.py --artifact-dir artifacts/<slug>-<trackId>
```

追问：

```bash
python3 scripts/qa_transcript.py --artifact-dir artifacts/<slug>-<trackId> --question "只想听他讲创业低谷的部分"
```

编排式运行：

```bash
python3 scripts/run_pipeline.py --query "lex fridman openai"
```

## 文件约定

每个单集对应一个目录：

```
artifacts/<slug>-<trackId>/
```

预期文件：

- `episode.json`
- `audio.wav`
- `transcript.txt`
- `transcript.segments.json`
- `transcript.srt`
- `analysis.md`
- `topics.json`
- `summary.json`

详细格式见 `references/artifact-contract.md`。
