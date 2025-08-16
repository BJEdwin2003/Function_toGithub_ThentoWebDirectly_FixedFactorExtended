
# 混合模型（MixedLM）+ 量产哨兵 + ML 残差修正 —— 阳极氧化 L*/a*/b* 方差收敛的统一框架（Part 2/2）

> **版本**：v2 (Quality-first)  
> **撰写时间**：2025-08-14

---

## 7. 建模细节（公式、估计、实现）

### 7.1 MixedLM 结构
- **固定效应（DOE 形态）**：
  \[ y = β0 + β_A A + β_C C + β_T T + β_{AA} A^2 + β_{CC} C^2 + β_{TT} T^2 + \sum β_{ij} X_i X_j + \sum γ_k Z_k + ε \]
  其中 `A/C/T` 代表 `dye1/dye2/Time/Temp`，`Z_k` 为协变量（如样条后的 `queue_delay_sec`、`bath_age_hours`、`ambient_T/RH`）。
- **固定效应（量产形态）**：
  \[ y = β0 + \sum γ_k Z_k + ε \]（四设参仅作为元数据记录；出现多水平后自动切回 DOE）
- **随机效应（交叉/分量方差）**：
  \[ u_{shift} + u_{load} + u_{x} + u_{y} (+ u_{tank}) \]  
  以 `vc_formula` 方式进入（哪些列存在就加入哪些方差分量）。
- **估计**：REML；顶层 `groups` 优先 `load_id`，否则 `rack_id`，都无则退化为单组。

### 7.2 协变量与样条
- `queue_delay_sec` 建议 **B‑spline**（df=4, degree=3, 无截距），可捕捉秒级偏差的非线性影响；
- 其余可观测量（`bath_age_hours/ambient_T/ambient_RH`）直接线性纳入，必要时标准化；
- 若考虑班次对时间偏差的不同敏感度，可引入交互 `shift × time_s#` 或按班次滚动两步法拟合。

### 7.3 稳健性与诊断（质量守门人）
- **稳健协方差**：HC3；
- **高杠杆/强影响点**：Cook’s D、DFBETAS；
- **共线性**：VIF（保层级规则，必要时岭/弹性网稳健化）；
- **LOF 近似**：作为模型结构适配性的二次证据；
- **残差图谱**：QQ、残差‑拟合、残差 vs 协变量；
- **组外验证**：`GroupKFold/LOGO`，分组键优先 `load`，无则用 `shift`。

### 7.4 尾部/分位建模（ΔE95、P95−P5）
- 在 MixedLM 残差上训练 **分位数 GBDT**（0.05/0.5/0.95），输出 **P95−P5** 与 **ΔE95** 的预测区间；
- 报告中给出 **覆盖率校验**（实际覆盖 ≈ 置信度）。

### 7.5 ML 残差修正（可插拔）
- 训练目标 1：直接预测 y（对照）；
- 训练目标 2：**预测 `resid_Mixed`**，最终 `ŷ = ŷ_Mixed + ŷ_ML(resid)`；
- 采用 **GroupKFold**，防止泄漏；
- 解释：SHAP/PDP/ICE 与 MixedLM 系数对照，检查一致性。

### 7.6 代码骨架（伪代码）
```python
# 关键步骤：自动判别形态 → 构造 vc_formula → MixedLM → 组外CV → 分位模型（可选）
mode = detect_mode(df)  # 'DOE' or 'PROD'
vc, groups = build_vc(df)
covars = build_covariates(df)  # B-spline for queue_delay_sec + others
rhs = formula_doe(covars) if mode=='DOE' else formula_prod(covars)
for y in ['Lvalue','Avalue','Bvalue']:
    m = fit_mixedlm(df, y, rhs, vc, groups)
    diagnostics = run_diagnostics(m, df, rhs)
    cv = group_cv_score(df, y, rhs, group_key='load_id' or 'shift')
    quantiles = fit_quantile_gbdt_on_residuals(df, y, m.resid)  # 可选
    export_reports(y, m, diagnostics, cv, quantiles)
```

---

## 8. 诊断与验收指标（写入报告首页）
- **结构适配**：LOF 通过（p ≥ 0.10）或给出改模建议；
- **稳健性**：HC3 下显著性稳定；高杠杆点占比 < 阈值，强影响点已标注；
- **共线性**：VIF < 5（或说明已用岭/弹性网稳健化）；
- **组外性能**：按 `load/shift` 组外 MAE/RMSE 优于 OLS 基线；
- **能力与尾部**：`P95−P5`、`ΔE95` **下降 ≥ 目标值**；分层 Ppk 提升且覆盖率与预期一致（预测 PI 的覆盖接近置信度）。

---

## 9. 部署与接口（保持现网习惯）

### 9.1 `/runDOE` 不变
- 仍接收 `multipart/form-data` 上传 CSV；
- 返回体延用既有字段（`status/files/console_output`），新增字段置于 `optional`，完全兼容前端。

### 9.2 前端只加“提示与模板下载”
- `doe_analysis_test_interface.html` 增加 **“可选列说明 + CSV 模板下载”**；
- 上传逻辑/文件浏览/下载接口不变。

### 9.3 文件产出（与现网对齐）
- `uncoded_parameters.csv`、`fullmodel_logworth.csv`、`simplified_logworth.csv`（若处于 DOE）；
- `mixed_model_variance_summary.csv`（各随机项方差分量/ICC/BLUP 概览）；
- `diagnostics_summary.csv`（HC3、Cook’s D、VIF、LOF、CV 指标）；
- `quantile_tail_summary.csv`（P95−P5/ΔE95 与覆盖率）；
- 各响应的残差与预测导出：`residual_data_L.csv` 等；
- 图表（PNG）：效应图/曲面、位置热力图、雷达图、QQ/残差图、滚动监控折线等。

---

## 10. 风险与弯路复盘（经验教训）

1) **只做最小改造**的隐性风险：
   - 容易忽略 **组外泛化**、**异方差**、**尾部风险**；
   - 未来想引入 ML/漂移监控时缺乏插槽与治理点。
2) **把随机结构当“装饰项”** 的误区：
   - 高载位点差异是主导方差源之一（已被仿真与现场证实）；
   - 不纳入 `shift/load/位置/tank` 就无法解释“100>24”的离散放大。
3) **量产后只盯均值** 的风险：
   - 真实改进目标是 **分布收窄**（P95−P5、ΔE95、分层 Ppk），均值命中不代表外观一致；
4) **把 ML 当“万能钥匙”**：
   - 先有统计解释与方差分解，再用 ML 补盲是更稳的**双引擎**路径。

---

## 11. 路线图（建议）

- **Week 0–1**：落地 V2 内核（形态判别 + MixedLM + 稳健诊断 + 组外 CV + 文件/图表）；
- **Week 2–3**：上线 **分位尾部模块** 与 **滚动监控**；
- **Week 4–6**：引入 **ML 残差修正**（XGBoost/LightGBM/BART）与 **覆盖率验证**；
- **Week 6+**：漂移检测、推荐器（小步设参建议）、A/B 与合规模块。

---

## 12. 交付物清单（你现在就能拿到）
- `doe_template.csv`（运行/测量双表示例，含必选/可选列）；
- `mixed_model_core_v2.py`（质量优先内核，自动形态、交叉随机、协变量样条、诊断与导出框架）；
- `README.md`（本文件 Part 1/2 + Part 2/2）；
- 报告样式（PNG/CSV 命名规范，与现网一致）。

---

## 13. 参考与注释
- [R1] `doe_analysis_test_interface.html`（端点/字段/下载入口）
- [R2] `MixedModelDOE_Web_V1.html`（端点/字段/下载入口）
- [R3] （同 R2 的团队分享版本）
- [R4] 《Mixed Model DOE 项目完整架构解析》（HTML→app.py→Core）
- [R5] 《Mixed Model DOE AI Agent 项目可行性说明书》（目标与架构）
- [R6] 《Color S2 DOE 建模方法论背景说明（JMP→Mixed Model 的动因）》
- [R7] 《阳极氧化仿真报告_20250226》（阴极/挡板优化、厚度均匀性）

---

### 附录 A：接口与数据契约要点（可贴到前端页面）
```text
必选：dye1,dye2,Time,Temp,Lvalue,Avalue,Bvalue
强烈建议（量产/高载）：shift,load_id,flybarX,flybarY,entry_timestamp,queue_delay_sec,bath_age_hours,ambient_T,ambient_RH
可选：tank_id,config
形态自动判别：四设参若为单值→量产形态；出现多水平→DOE 形态。
```

### 附录 B：常见问答
- **Q：只有一个最优 config 时还需要 ML 吗？**  
  A：需要与否取决于目标。若只做监控与解释，MixedLM 足够；若要**尾部收紧/预警**，引入 **分位模型** 或 **ML 残差修正**会更稳健。
- **Q：如何证明“100>24”的离散放大来自位置/班次/槽位？**  
  A：在同一数据集上，比较 `Var(flybarX)`、`Var(flybarY)`、`Var(shift)` 在 24 vs 100 条件下的方差分量；结合仿真报告与位点热力图给出一致性证据。

---

> **结语**：本 v2 框架以 **质量优先** 为原则，统一了 DOE 与量产两种形态，并为 ML 的渐进式引入留出了工程化的插槽与治理边界。它兼顾统计解释、工程可行与运维稳健，适配你们阳极氧化高载条件下的真实变差结构。
