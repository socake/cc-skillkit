# cc-skillkit

[English](README.md) | **中文**

> 一套个人的、可移植的 **Claude Code 技能合集** —— 把 DevOps、SRE、云治理和工程工作流
> 的技能打包成可安装插件。一条命令装到任何机器,无需克隆。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin%20marketplace-d97757)](https://code.claude.com/docs/en/plugin-marketplaces)
[![Validate](https://github.com/socake/cc-skillkit/actions/workflows/validate.yml/badge.svg)](https://github.com/socake/cc-skillkit/actions/workflows/validate.yml)

**13 个技能 · 3 个插件 · 1 条命令安装。** 🌐 [在线落地页](https://socake.github.io/cc-skillkit/)

技能(skill)是一组指令文件夹,Claude Code 按需加载,用可复现的方式完成专门任务。这个仓库
把我的技能打包成正规的 **插件市场(plugin marketplace)** —— 带版本、经 CI 校验、跨机器
可移植,而不是绑死在某台笔记本上的一堆软链。

## 安装

在任何装了 [Claude Code](https://code.claude.com) 的机器上 —— **无需克隆**。先注册市场一次,
再按需安装你想要的 toolkit:

```bash
claude plugin marketplace add socake/cc-skillkit

claude plugin install ops-toolkit@cc-skillkit       # K8s/EKS/ACK 排障、根因分析、Dockerfile 审查
claude plugin install cloud-toolkit@cc-skillkit     # AWS 成本扫描、IAM/RAM 审查
claude plugin install workflow-toolkit@cc-skillkit  # PR 描述、运维会话、画图、报告……
# 重启 Claude Code,然后:  claude plugin list
```

或从本地副本(开发用):`./scripts/install.sh`。卸载用 `./scripts/uninstall.sh`。

## 技能

### `ops-toolkit` — 排障与审查

| 技能 | 干什么 |
|------|--------|
| [`k8s-triage`](plugins/ops-toolkit/skills/k8s-triage/SKILL.md) | 对异常 Kubernetes 工作负载只读、证据优先地排障 —— 固定顺序,给有据的根因而非一堆日志。 |
| [`incident-rca`](plugins/ops-toolkit/skills/incident-rca/SKILL.md) | 系统化根因分析:时间线、变更关联、证据纪律下并行验证假设,产出根因卡或无指责复盘。 |
| [`eks-triage`](plugins/ops-toolkit/skills/eks-triage/SKILL.md) | EKS 特有排障:节点组不上线、VPC CNI 崩、IRSA/IAM 不足、Karpenter 不扩容、子网 IP 耗尽。 |
| [`ack-triage`](plugins/ops-toolkit/skills/ack-triage/SKILL.md) | 阿里云 ACK 特有排障:ECI 拉镜像超时、节点池、Terway CNI、CCM/SLB 无后端。 |
| [`dockerfile-audit`](plugins/ops-toolkit/skills/dockerfile-audit/SKILL.md) | 从安全/体积/可复现/可维护四轴审查 Dockerfile —— 按严重度给问题清单和修法。 |

### `cloud-toolkit` — 云治理

| 技能 | 干什么 |
|------|--------|
| [`aws-cost-scan`](plugins/cloud-toolkit/skills/aws-cost-scan/SKILL.md) | 只读扫 AWS 浪费 —— 闲置负载均衡、未关联 EIP、孤儿快照、超配节点池 —— 按月省钱额排序。 |
| [`ram-iam-audit`](plugins/cloud-toolkit/skills/ram-iam-audit/SKILL.md) | AWS IAM + 阿里云 RAM 最小权限审查 —— 通配 action、FullAccess 滥用、过期密钥、提权组合。 |

### `workflow-toolkit` — 工程工作流与产出

| 技能 | 干什么 |
|------|--------|
| [`pr-describe`](plugins/workflow-toolkit/skills/pr-describe/SKILL.md) | 把 diff 变成清晰、reviewer 友好的 PR 描述 —— what/why/how、风险、测试、回滚、关注点。 |
| [`ops-session`](plugins/workflow-toolkit/skills/ops-session/SKILL.md) | 结构化运维会话协议 —— Plan→RootCause→Action→Verify→Learn,弱根因硬阻断写操作、结论必带证据。 |
| [`task-kickoff`](plugins/workflow-toolkit/skills/task-kickoff/SKILL.md) | 复杂长任务开场协议 —— plan/implement 分离、人在环节点、两次失败止损、多轮验证。 |
| [`html-report`](plugins/workflow-toolkit/skills/html-report/SKILL.md) | 把长 markdown 报告渲染成精致的单文件 HTML —— 卡片、表格、可折叠区、筛选 chip。 |
| [`drawio-arch`](plugins/workflow-toolkit/skills/drawio-arch/SKILL.md) | 端到端用 draw.io 出图 —— 架构/流程/拓扑 —— CLI 渲染 PNG/SVG,带语义化样式体系。 |
| [`browser-verify`](plugins/workflow-toolkit/skills/browser-verify/SKILL.md) | 容器化真实浏览器 e2e 验证(CDP) —— 走点击流程、抓 console/network、关联后端日志,给过/挂结论。 |

_每个技能都脱敏、不含任何密钥。_

## 加自己的技能

```bash
./scripts/new-skill.sh my-skill ops-toolkit   # 生成一个合规的 SKILL.md 骨架
$EDITOR plugins/ops-toolkit/skills/my-skill/SKILL.md
./scripts/install.sh                            # 重新加载
```

编写规范见 [`CLAUDE.md`](CLAUDE.md);CI 会强制校验。

## 为什么用市场(而不是软链)?

- **可移植** —— `marketplace add socake/cc-skillkit` 在全新机器上零本地状态即可用,不含任何绝对路径。
- **带版本 · 经校验** —— 每个插件语义化版本;[CI](.github/workflows/validate.yml) 在每次 push
  校验每个 `SKILL.md` 的 frontmatter、命名和 manifest 一致性。
- **一条命令的生命周期** —— 安装 / 更新 / 卸载 / 启用 / 禁用,全走官方 `claude plugin` CLI。

设计说明与取舍:[`docs/design.md`](docs/design.md)。

## 仓库结构

```
.claude-plugin/marketplace.json   市场入口(列出各插件)
plugins/<plugin>/
  .claude-plugin/plugin.json      插件清单
  skills/<skill>/SKILL.md         一个技能(+ 可选 references/、assets/)
scripts/                          install · uninstall · new-skill · validate
site/                             GitHub Pages 落地页
.github/workflows/                validate.yml(CI) · pages.yml(部署)
CLAUDE.md                         编写指南
```

## 许可证

[MIT](LICENSE) © Wenzhuo Huang
