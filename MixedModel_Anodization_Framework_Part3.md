
# 混合模型（MixedLM）+ ML 可扩展增强 —— 动态因子注册与负载异方差处理（Part 3/3）

> **版本**：v2.1 (Quality-first, Extensible)  
> **撰写时间**：2025-08-14  
> **作者**：Edwin ZhangLei & Copilot（协作）

本 Part 3 承接 **Part 1/2** 与 **Part 2/2**：
- 解决 **固定因子可扩展** 的需求（`dye3/dye4/...` 或新增其他工艺因子，如 `pressure/speed/...`），在**不改接口**的前提下实现**动态因子注册（registry）**与 **RSM 自动构建**；
- 给出 **满载 vs 非满载（24 vs 100 件）** 导致**方差变化**（异方差 + 方差分量差异）的**统计与 ML 兼容处理**；
- 补齐 **API 扩展、代码骨架、报告新增、上线步骤与验证计划**。

---

## 1. 设计目标与边界

1) **可扩展**：不硬编码因子名，自动从 CSV 列或 `schema.fixed_factors` 中识别“可控因子”；对**数值型**自动生成 **RSM（线性+二次+交互）**，对**类别型**自动 `C(var)`。  
2) **形态自适应**：若所有可控因子均为单一水平，即进入**量产形态**（仅协变量 + 随机结构）；出现多水平自动回到 **DOE 形态**。  
3) **统计与 ML 共用特征层**：把 RSM 展开的项作为 **显式特征**供 ML 复用；保证“解释与预测”一致。  
4) **负载导致的异方差**：在 **均值模型**中显式加入负载特征与位置交互；在 **方差模型**中用 FGLS 两阶段对 `log(e^2)` 建模并加权再拟合。  
5) **接口兼容**：`/runDOE` 不变；可选 JSON `schema` 让前端/Agent 显式指定固定因子列表与超参；老 CSV 完全可跑。

---

## 2. 动态因子注册（registry）与 RSM 自动构建

### 2.1 自动识别规则
- **默认推断**：匹配正则 `^(dye\d+|Time|Temp|pressure|speed)$`（可在配置中扩展）；  
- **显式指定**：请求体中 **可选** JSON：
```json
{
  "schema": {
    "fixed_factors": ["dye1","dye2","dye3","Time","Temp"],
    "interactions": "numeric_only",   
    "spline": {"queue_delay_sec": {"df": 4, "degree": 3}},
    "load_features": ["pieces_per_bar","load_ratio","is_full"],
    "enable_fgls": true
  }
}
```
> 若 `schema` 缺省，则采用“默认推断”。

### 2.2 RSM 项生成（遵循层级/Heredity）
- **线性项**：所有数值因子 + 类别因子 `C(var)`；  
- **二次项**：所有数值因子 `I(x**2)`；  
- **交互项**：默认“数值‑数值”的二阶交互；如需考虑与 `C(var)` 的交互，可在 `schema.interactions` 打开。  
- **层级约束**：简化/筛选时，若保留交互或二次项，**必须**保留相应主效应。  

### 2.3 形态判别（自动）
- 统计可控因子的**基数/跨度**：若全部为单一水平（或跨度 < ε），则 **PROD**；只要出现多水平，**DOE**。  
- 与 Part 1/2 的判别逻辑一致，前端无需 UI 切换。

---

## 3. 负载（24 vs 100）导致的异方差：统计与 ML 兼容处理

### 3.1 均值模型（MixedLM）中的负载特征
- 建议新增：`pieces_per_bar`、`load_ratio = 件数/最大位点数`、`is_full（0/1）`；  
- **固定效应**加入负载特征，并与位置交互：`load_ratio:flybarX`、`load_ratio:flybarY`；  
- **随机结构**不变：`groups=load_id`；`vc_formula` 包含 `shift/flybarX/flybarY/tank/config`（列有就上）。  

### 3.2 方差模型（FGLS 两阶段）
- **阶段 1**：MixedLM 拟合均值模型，得残差 `e`；  
- **阶段 2**：对 `log(e^2+ε)` 建模（可含 `bs(load_ratio)`/位置/班次），得到 `pred_logvar`，设权重 `w=exp(-pred_logvar)`；用 `w` **再拟合**（加权近似 FGLS）。  
- 产物：更稳健的系数与更高效的方差估计；报告中增加 `logvar_model_summary.csv` 与 **按负载切片**的 P95−P5/ΔE95。  

### 3.3 ML 侧兼容
- **特征层**：与统计共用（RSM 展开的项 + 负载 + 位置 + 班次 + 协变量）。  
- **训练策略**：
  - **单一模型**：同一模型中学习负载效应（支持分位回归/异方差 loss）；
  - **分段模型**：满载/非满载分别建模，解释更清晰。  
- **验证**：按 `load_id/shift` 的 GroupKFold；**按负载切片**报告 MAE/RMSE/覆盖率。  
- **稳定性**：可对 `load_ratio` 加**单调性约束**（如果工艺知识要求）。

---

## 4. API 兼容与数据契约（扩展不破坏旧版）

- `/runDOE` 继续接收 `multipart/form-data`，**不要求**提供 `schema`；  
- 若同时上传同名 JSON 字段 `schema`，后端优先使用显式定义（否则自动推断）；  
- **CSV 列**（最少）：`Lvalue,Avalue,Bvalue` + 你已有的 `dye1/dye2/Time/Temp`；  
- **可选列**（强烈建议量产/高载提供）：`shift,load_id,flybarX,flybarY,entry_timestamp,queue_delay_sec,bath_age_hours,ambient_T,ambient_RH,` 以及 `pieces_per_bar,load_ratio,is_full,tank_id,config`。  

> **向后兼容**：老 CSV 只含四设参也能跑；新增 `dye3/dye4` 或 `pressure/speed` 只需新增列，无需改前端。

---

## 5. 代码骨架（关键片段）

> 以下片段可并入 `mixed_model_core_v2.py`，与 Part 1/2 的骨架一致。

```python
import re, numpy as np, pandas as pd
import statsmodels.formula.api as smf
from patsy import dmatrix

# (1) 自动识别可控因子
PAT = re.compile(r"^(dye\d+|Time|Temp|pressure|speed)$", re.I)

def infer_fixed_factors(df, explicit=None):
    cols = explicit if explicit else [c for c in df.columns if PAT.match(c)]
    num = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    cat = [c for c in cols if c not in num]
    return num, cat

# (2) RSM 生成

def build_rsm(num, cat, numeric_interact=True):
    linear = num[:] + [f"C({c})" for c in cat]
    square = [f"I({x}**2)" for x in num]
    inter = []
    if numeric_interact:
        for i,a in enumerate(num):
            for b in num[i+1:]:
                inter.append(f"{a}:{b}")
    return linear + square + inter

# (3) 协变量（含样条与负载特征）

def build_covars(df):
    cov = []
    if "queue_delay_sec" in df.columns:
        df["qd_min"] = df["queue_delay_sec"]/60.0
        bs = dmatrix("bs(qd_min, df=4, degree=3, include_intercept=False)", df, return_type='dataframe')
        for i,c in enumerate(bs.columns,1):
            df[f"qd_s{i}"] = bs[c]
        cov += [f"qd_s{i}" for i in range(1, bs.shape[1]+1)]
    for c in ["bath_age_hours","ambient_T","ambient_RH","pieces_per_bar","load_ratio","is_full"]:
        if c in df.columns: cov.append(c)
    # 负载×位置交互
    for pos in ["flybarX","flybarY"]:
        if pos in df.columns and "load_ratio" in df.columns:
            df[f"lr_{pos}"] = df[pos]*df["load_ratio"]
            cov.append(f"lr_{pos}")
    return cov

# (4) 形态判别 + RHS

def assemble_rhs(df, fixed_terms, covars, eps=1e-6):
    # 判断固定因子是否全部“单一水平”
    base_cols = [t for t in fixed_terms if ":" not in t and not t.startswith("I(")]
    uniq = [df[c].nunique(dropna=True) if c in df.columns else 1 for c in base_cols]
    is_prod = all(u<=1 for u in uniq)
    if is_prod:
        rhs = " + ".join(covars) if covars else "1"
        mode = "PROD"
    else:
        rhs = " + ".join((fixed_terms+covars) if covars else fixed_terms)
        mode = "DOE"
    return rhs, mode

# (5) 随机结构

def build_vc_groups(df):
    vc = {}
    for cat in ["shift","flybarX","flybarY","tank_id","config"]:
        if cat in df.columns:
            vc[cat] = f"0 + C({cat})"
    if "load_id" in df.columns: groups = df["load_id"]
    elif "rack_id" in df.columns: groups = df["rack_id"]
    else: groups = pd.Series(1, index=df.index)
    return (vc if len(vc)>0 else None), groups

# (6) FGLS 两阶段（可选）

def fit_mixedlm_fgls(df, y, rhs, vc, groups, enable_fgls=False):
    md = smf.mixedlm(f"{y} ~ {rhs}", df, groups=groups, vc_formula=vc, re_formula="1")
    m  = md.fit(method="lbfgs", reml=True)
    if not enable_fgls: return m, None
    eps = 1e-8
    df["_e2"] = m.resid.values**2 + eps
    rhs_var = []
    for v in ["load_ratio","flybarX","flybarY"]:
        if v in df.columns: rhs_var.append(v)
    if "shift" in df.columns: rhs_var.append("C(shift)")
    var_formula = ("np.log(_e2) ~ "+" + ".join(rhs_var)) if rhs_var else "np.log(_e2) ~ 1"
    aux = smf.ols(var_formula, data=df).fit()
    w = np.exp(-aux.fittedvalues)  # 1/Var
    wls = smf.wls(f"{y} ~ {rhs}", data=df, weights=w).fit()  # 近似 FGLS
    return m, wls
```

---

## 6. 报告新增与可视化
- `variance_components_by_load.csv`：24 vs 100（或不同 `load_ratio` 段）的 `Var(shift/flybarX/flybarY/tank)` 对比；  
- `logvar_model_summary.csv`：异方差（logvar）模型的系数重要性；  
- `by_load_tail_metrics.csv`：按负载切片的 **P95−P5**、**ΔE95**、覆盖率；  
- 图表：负载‑位置交互热力图、按负载分段的尾部指标折线、BLUP 位置校正对比图等。

---

## 7. 上线步骤（不改接口）
1) 将本 Part 3 的代码片段并入 `mixed_model_core_v2.py`：新增 **registry/RSM 生成器/负载特征/FGLS**；  
2) `app.py` 保持 `/runDOE` 不变，仅将核心调用指向 **v2 内核**；  
3) 在前端页面增加“**模板下载**/可选列说明”（无需改上传逻辑）；  
4) 在 Render 上做冒烟：上传 **24 vs 100** 两批 CSV，检查“形态判别、方差分量、尾部指标、报告文件”。

---

## 8. 验证计划（24 vs 100 件）
- **统计层**：
  - 观察 `Var(flybarX/flybarY/shift)` 是否在 100 件时显著上升；
  - FGLS 与未加权结果对比：系数稳定性、残差异方差缩减；
- **尾部层**：
  - P95−P5、ΔE95 在 100 件下的增长幅度与覆盖率；
- **ML 层**：
  - 单一模型 vs 分段模型（满载/非满载）的组外性能与可解释性对比；
  - 加单调约束后对高载段稳定性的提升。

---

## 9. 常见边界与错误防御
- 列缺失：若某些随机/协变量缺失，引擎自动降级并在 `diagnostics_summary.csv` 标注；  
- 多重共线性：报告 VIF，必要时启用岭/弹性网（或删除冗余项）；  
- 极端不平衡：当 `load_ratio` 或 `shift` 某些水平样本过少，切换到分段模型或启用分层抽样；  
- 过拟合防御：固定“层级规则”，限制交互阶数，并用 **GroupKFold** 做组外评估。

---

## 10. 参考与注释（与前两部分一致）
- [R1] `doe_analysis_test_interface.html`（端点/字段/下载入口）  
- [R2] `MixedModelDOE_Web_V1.html`（端点/字段/下载入口）  
- [R3] （同 R2 的团队分享版本）  
- [R4] 《Mixed Model DOE 项目完整架构解析》（HTML→app.py→Core）  
- [R5] 《Mixed Model DOE AI Agent 项目可行性说明书》（目标与架构）  
- [R6] 《Color S2 DOE 建模方法论背景说明（JMP→Mixed Model 的动因）》  
- [R7] 《阳极氧化仿真报告_20250226》（阴极/挡板优化、厚度均匀性）  

---

> **结语**：本 Part 3 完成了对 **动态因子扩展** 与 **负载异方差** 的工程化处理，并保持与前两部分一致的接口与方法论。至此，**同一引擎**即可覆盖：DOE 寻优 → 量产哨兵 → 高载异方差 → 渐进式 ML。
