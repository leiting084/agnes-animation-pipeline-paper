# Character-Consistent Animated Series Production with Generative Models: Failure Analysis at Episode Scale

S01E01 的 AI 动画生产流水线，附 52 个镜头的审核记录。

## 内容

```
├── main.tex                # 论文源码 · IEEEtran 版
├── main_mtap.tex           # 论文源码 · llncs 版
├── preamble.tex            # 宏包与全篇统一命令
├── affiliation.tex         # 🔒 本地真实单位，被 .gitignore 拦截，不在仓库里
├── sections/               # 章节，一章一文件（02–07 为编译占位，待写）
├── figures/  bib/          # make 时自动创建，bib/references.bib 为空库占位
├── data/                   # 原始数据
│   └── audit_records_s01e01.json
└── code/
    └── classify_failure_modes.py
```

编译：`make mtap`（期刊版）/ `make icme`（会议版），PDF 出到 `build/`。
clone 后无需任何配置，`affiliation.tex` 不存在时 LaTeX 自动回落占位值，照样能编译。

## 数据

`data/audit_records_s01e01.json`：52 条镜头审核记录，6 个场景（s76 / s80 / s90 / s100 / s101 / s102），
每个字段见 JSON 自身；每条记录内嵌 `probe_raw`（生成时的完整 ComfyUI 工作流），可逐条复现。

判定口径为 `in_v9_final` 字段（是否进入 v9 终版）。

**⚠️ 使用前必读**：`s76 / s80 / s90` 是场景号，不是批次号。这三个场景 100% 判退，`s100` 通过率 83%。
跨场景直接求聚合指标，会把场景内容差异误判成方法有效性差异。做对比请先分层。

## 引用

```bibtex
@misc{agnes_anime_pipeline_2026,
  author       = {风云变色z},
  title        = {Character-Consistent Animated Series Production with Generative Models:
                  Failure Analysis at Episode Scale},
  year         = {2026},
  publisher    = {GitHub},
  howpublished = {https://github.com/leiting084/agnes-animation-pipeline-paper}
}
```

- 代码（MIT）与数据（`data/DATA_LICENSE.md`）可自由引用。
- 分析结论尚未发表，引用请等论文见刊。
- 真实作者名与单位见论文正式发表版本，本仓库不提供。

## 联系

93671248@qq.com · 问题优先开 Issue。
