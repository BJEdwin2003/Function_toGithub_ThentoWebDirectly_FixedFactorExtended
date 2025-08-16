import pandas as pd
import numpy as np
from itertools import combinations
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from patsy import dmatrix
from statsmodels.stats.outliers_influence import OLSInfluence
from scipy.stats import f
import warnings
warnings.filterwarnings("ignore")

from statsmodels.formula.api import mixedlm
from statsmodels.tools.sm_exceptions import ConvergenceWarning
warnings.simplefilter("ignore", ConvergenceWarning)
import os
import sys
from io import StringIO

def run_mixed_model_doe_with_output(file_path, output_dir, predictors=None, response_vars=None):
    # 对X、Y变量名做strip和str转换，去除前后空格，确保和强制赋值时一致
    if predictors:
        predictors = [str(x).strip() for x in predictors]
    if response_vars:
        response_vars = [str(y).strip() for y in response_vars]
    print(f"[DEBUG] Cleaned predictors: {predictors}")
    print(f"[DEBUG] Cleaned response_vars: {response_vars}")
    """
    基于原始MixedModelDOE_Function_FollowOriginal_20250804.py的Web输出版本
    专门用于捕获控制台输出并返回给Web界面显示
    
    新增功能：
    1. 捕获所有控制台输出
    2. 返回格式化的分析结果文本
    3. 保存控制台输出到文件
    4. 保持原始分析逻辑不变
    """
    
    # 🔧 捕获所有控制台输出
    console_output = StringIO()
    original_stdout = sys.stdout
    
    # 重定向输出到StringIO
    sys.stdout = console_output
    
    # 用户必须显式选择 predictors (X) 和 response_vars (Y)
    if not predictors or not isinstance(predictors, list) or len(predictors) == 0:
        raise ValueError("必须选择至少一个预测因子 (X)。请在界面上选择X变量！")
    if not response_vars or not isinstance(response_vars, list) or len(response_vars) == 0:
        raise ValueError("必须选择至少一个响应变量 (Y)。请在界面上选择Y变量！")
    group_keys = predictors.copy()  # 分组键动态跟随X

    try:
        # === 1. 数据导入 ===
        df_raw = pd.read_csv(file_path)
        # 只保留数值型predictors
        valid_predictors = [col for col in predictors if col in df_raw.columns and pd.api.types.is_numeric_dtype(df_raw[col])]
        if not valid_predictors:
            raise ValueError("无有效数值型预测因子可用于建模！")
        predictors = valid_predictors

        print("🚀 开始DOE混合模型分析...")
        print(f"📊 数据文件: {file_path}")
        print(f"📈 响应变量: {response_vars}")
        print(f"🔧 预测因子: {predictors}")
        print(f"📏 数据维度: {df_raw.shape}")

        # === 2. 标准化用于 simplified 模型建模 ===
        scaler = StandardScaler()
        df = df_raw.copy()
        df[predictors] = scaler.fit_transform(df[predictors])

        print("\n✅ 数据标准化完成")
        print("📏 标准化后的统计信息:")
        print(f"   均值: {df[predictors].mean().values}")
        print(f"   标准差: {df[predictors].std(ddof=0).values}")
        print(f"   原始均值 (X_mean): {scaler.mean_}")
        print(f"   原始标准差 (X_std): {scaler.scale_}")

        # === 6. 构造原始 Config 键值（JMP 对齐）===
        # 自动兼容 group_keys: 单列直接用，多列组合
        valid_group_keys = [col for col in group_keys if col in df_raw.columns]
        if not valid_group_keys:
            # fallback: use default
            valid_group_keys = ["dye1", "dye2", "dye3", "Time", "Temp"]
        if len(valid_group_keys) == 1:
            df_raw["Config_combo"] = df_raw[valid_group_keys[0]].astype(str)
        else:
            df_raw["Config_combo"] = df_raw[valid_group_keys].astype(str).agg("_".join, axis=1)
        df["Config_combo"] = df_raw["Config_combo"]

        # === 3. 构造 RSM 项 ===
        def create_rsm_terms(terms):
            linear = terms
            square = [f"I({t}**2)" for t in terms]
            inter = [f"{a}:{b}" for a, b in combinations(terms, 2)]
            return linear + square + inter

        rsm_terms = create_rsm_terms(predictors)
        print(f"\n🔧 构造RSM项: {len(rsm_terms)}个项")
        print(f"   线性项: {predictors}")
        print(f"   平方项: {[f'I({t}**2)' for t in predictors]}")
        print(f"   交互项: {[f'{a}:{b}' for a, b in combinations(predictors, 2)]}")

        # === 4. 全模型 LogWorth 扫描 ===
        print("\n📊 开始全模型LogWorth分析...")
        effect_summary_all = pd.DataFrame()
        for y in response_vars:
            formula = f"{y} ~ " + " + ".join(rsm_terms)
            model = smf.ols(formula, data=df).fit()
            anova_tbl = anova_lm(model, typ=3).reset_index()
            anova_tbl = anova_tbl.rename(columns={"index": "Factor"})
            anova_tbl = anova_tbl[anova_tbl["Factor"] != "Residual"]
            anova_tbl["LogWorth"] = -np.log10(anova_tbl["PR(>F)"].replace(0, 1e-16))
            temp = anova_tbl[["Factor", "LogWorth"]].copy()
            temp.columns = ["Factor", y]
            effect_summary_all = pd.merge(effect_summary_all, temp, on="Factor", how="outer") if not effect_summary_all.empty else temp

        effect_summary_all = effect_summary_all.fillna(0)
        effect_summary_all["Median_LogWorth"] = effect_summary_all[response_vars].median(axis=1)
        effect_summary_all["Max_LogWorth"] = effect_summary_all[response_vars].max(axis=1)
        effect_summary_all["Appears_Significant"] = (effect_summary_all[response_vars] > 1.3).sum(axis=1)
        effect_summary_all = effect_summary_all.sort_values("Max_LogWorth", ascending=False)

        # === 5. 筛选简化因子（保持 hierarchy）===
        def get_simplified_factors(effect_matrix, threshold=1.3, min_significant=2):
            factors = effect_matrix[
                (effect_matrix["Max_LogWorth"] >= threshold) | 
                (effect_matrix["Appears_Significant"] >= min_significant)
            ]["Factor"].tolist()
            if "Intercept" in factors:
                factors.remove("Intercept")
            hierarchical_terms = set(factors)
            for f in factors:
                if ":" in f:
                    a, b = f.split(":")
                    hierarchical_terms |= {a.strip(), b.strip()}
                if "I(" in f:
                    base = f.split("(")[1].split("**")[0].strip()
                    hierarchical_terms.add(base)
            return sorted(hierarchical_terms)

        simplified_factors = get_simplified_factors(effect_summary_all)

    # ...existing code...

        # === 7. 共线性检查 ===
        try:
            x = dmatrix(" + ".join(simplified_factors), data=df, return_type="dataframe")
            xtx = x.T @ x
            condition_number = np.linalg.cond(xtx.values)
            print(f"\n📐 共线性检查 - X'X条件数: {condition_number:.2f}")
        except Exception as e:
            print(f"\n❌ 设计矩阵构建错误: {str(e)}")
            condition_number = float('inf')

        # === 8. 打印输出：Full Model + Simplified Model LogWorth ===
        print("\n" + "="*80)
        print("📊 全模型效应汇总表 (LogWorth)")
        print("="*80)
        print(effect_summary_all.to_string(index=False))

        print(f"\n✅ 建议的简化因子 (含层次结构): {simplified_factors}")
        print(f"📐 共线性检查 - X'X条件数: {condition_number:.2f}")

        # 构建 simplified_logworth_df
        simplified_logworth_df = pd.DataFrame()
        for y in response_vars:
            print(f"\n🔍 构建简化模型: {y}")
            formula = f"{y} ~ " + " + ".join(simplified_factors)
            model = smf.ols(formula=formula, data=df).fit()
            anova_tbl = anova_lm(model, typ=3).reset_index()
            anova_tbl = anova_tbl.rename(columns={"index": "Factor"})
            anova_tbl = anova_tbl[anova_tbl["Factor"] != "Residual"]
            anova_tbl["LogWorth"] = -np.log10(anova_tbl["PR(>F)"].replace(0, 1e-16))
            temp = anova_tbl[["Factor", "LogWorth"]].copy()
            temp.columns = ["Factor", y]
            simplified_logworth_df = pd.merge(simplified_logworth_df, temp, on="Factor", how="outer") if not simplified_logworth_df.empty else temp

        simplified_logworth_df = simplified_logworth_df.fillna(0)
        simplified_logworth_df["Median_LogWorth"] = simplified_logworth_df[response_vars].median(axis=1)
        simplified_logworth_df["Max_LogWorth"] = simplified_logworth_df[response_vars].max(axis=1)
        simplified_logworth_df["Appears_Significant"] = (simplified_logworth_df[response_vars] > 1.3).sum(axis=1)
        simplified_logworth_df = simplified_logworth_df.sort_values("Max_LogWorth", ascending=False)

        print("\n" + "="*80)
        print("📊 简化模型效应汇总表 (LogWorth)")
        print("="*80)
        print(simplified_logworth_df.to_string(index=False))

        # === Part 2: 混合模型建模与诊断 ===
        print("\n" + "="*80)
        print("🔧 开始混合效应模型拟合")
        print("="*80)

        models = {}
        param_coded_list = []
        param_uncoded_list = []
        diagnostics_summary = []
        var_records = []
        lof_records = []

        for y in response_vars:
            try:
                print(f"\n🔧 拟合混合模型: {y}")
                # 构建 Mixed Model（含 Config_combo 为随机组变量）
                formula = f"{y} ~ " + " + ".join(simplified_factors)
                model = mixedlm(formula, data=df, groups=df["Config_combo"])
                model_fit = model.fit(reml=True)
                
                # 方差组分（用于诊断）
                group_var = model_fit.cov_re.iloc[0, 0] if model_fit.cov_re.shape[0] > 0 else np.nan
                residual_var = model_fit.scale  # == RMSE²
                
                print(f"📊 方差组分 - {y}:")
                print(f"   组间方差 (Config): {group_var:.4f}")
                print(f"   残差方差 (Error): {residual_var:.4f}")
                print(f"   RMSE: {np.sqrt(residual_var):.4f}")

                var_records.append({
                    "Response": y,
                    "Group_Var": group_var,
                    "Residual_Var": residual_var,
                    "RMSE_from_Var": np.sqrt(residual_var)
                })

                models[y] = model_fit

                y_true = df[y]
                y_pred = model_fit.fittedvalues
                resid = y_true - y_pred

                # 近似 R²
                ss_total = np.sum((y_true - y_true.mean()) ** 2)
                ss_resid = np.sum((y_true - y_pred) ** 2)
                r_squared = 1 - ss_resid / ss_total

                # Adjusted R² 近似
                k = model_fit.k_fe - 1
                n = len(y_true)
                adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)
                rmse = np.sqrt(np.mean(resid ** 2))

                diagnostics_summary.append({
                    "Response": y,
                    "R2_Approximate": r_squared,
                    "Adjusted_R2_Approximate": adj_r_squared,
                    "RMSE": rmse,
                    "Mean_Response": y_true.mean(),
                    "Observations": n
                })

                # 解析固定效应参数表
                coef_tbl = model_fit.summary().tables[1].copy()
                coef_tbl.columns = ["Coef.", "Std.Err.", "z", "P>|z|", "[0.025", "0.975]"]
                coef_tbl["P>|z|"] = pd.to_numeric(coef_tbl["P>|z|"], errors="coerce").fillna(1.0)
                coef_tbl["Response"] = y
                coef_tbl["Factor"] = coef_tbl.index
                coef_tbl["LogWorth"] = -np.log10(coef_tbl["P>|z|"].replace(0, 1e-16))
                param_coded_list.append(coef_tbl[["Response", "Factor", "Coef.", "P>|z|", "LogWorth"]])

                # 参数反标准化（解码）
                X_mean = scaler.mean_
                X_scale = scaler.scale_
                uncoded = []

                for pname in coef_tbl.index:
                    if pname == "Intercept":
                        continue
                    try:
                        coef_coded = float(coef_tbl.loc[pname, "Coef."])
                    except:
                        continue

                    if pname.startswith("I("):
                        var = pname.split("(")[1].split("**")[0].strip()
                        if var not in predictors: continue
                        i = predictors.index(var)
                        beta_uncoded = coef_coded / (X_scale[i] ** 2)

                    elif ":" in pname:
                        var1, var2 = pname.split(":")
                        if var1 not in predictors or var2 not in predictors: continue
                        i1, i2 = predictors.index(var1), predictors.index(var2)
                        beta_uncoded = coef_coded / (X_scale[i1] * X_scale[i2])

                    else:
                        var = pname.strip()
                        if var not in predictors: continue
                        i = predictors.index(var)
                        beta_uncoded = coef_coded / X_scale[i]

                    uncoded.append((pname, beta_uncoded))

                intercept_uncoded = y_true.mean()
                for pname, beta_uncoded in uncoded:
                    if pname.startswith("I(") or ":" in pname: continue
                    var = pname.strip()
                    if var not in predictors: continue
                    i = predictors.index(var)
                    intercept_uncoded -= beta_uncoded * X_mean[i]

                uncoded.insert(0, ("Intercept", intercept_uncoded))
                uncoded_df = pd.DataFrame(uncoded, columns=["Factor", "Estimate"])
                uncoded_df["Response"] = y
                param_uncoded_list.append(uncoded_df)

                # JMP 风格 LOF 分析
                df_raw["_fitted"] = y_pred
                group_df = df_raw.groupby("Config_combo").agg(
                    local_avg=(y, "mean"),
                    fitted_val=("_fitted", "mean"),
                    count=("Config_combo", "count")
                ).reset_index()

                ss_lack = (group_df["count"] * (group_df["local_avg"] - group_df["fitted_val"])**2).sum()
                df_lack = len(group_df) - model_fit.df_modelwc - 1
                df_merge = df_raw.merge(group_df[["Config_combo", "local_avg"]], on="Config_combo", how="left")
                ss_pure = ((df_merge[y] - df_merge["local_avg"])**2).sum()
                df_pure = df_merge.shape[0] - len(group_df)

                ms_lack = ss_lack / df_lack if df_lack > 0 else 0
                ms_pure = ss_pure / df_pure if df_pure > 0 else 0
                F_lof = ms_lack / ms_pure if ms_pure > 0 else 0
                
                from scipy.stats import f as f_dist
                p_lof = 1 - f_dist.cdf(F_lof, df_lack, df_pure) if F_lof > 0 else 1.0

                lof_records.append({
                    "Response": y,
                    "DF_LackOfFit": df_lack,
                    "SS_LackOfFit": ss_lack,
                    "MS_LackOfFit": ms_lack,
                    "DF_PureError": df_pure,
                    "SS_PureError": ss_pure,
                    "MS_PureError": ms_pure,
                    "F_Ratio": F_lof,
                    "p_Value": p_lof
                })

            except Exception as e:
                print(f"❌ 模型拟合失败 - {y}: {e}")

        # === 诊断汇总输出 ===
        print("\n" + "="*80)
        print("📋 JMP风格诊断汇总")
        print("="*80)

        for diag, uncoded_df in zip(diagnostics_summary, param_uncoded_list):
            y = diag["Response"]
            print(f"\n▶ 响应变量: {y}")
            print("-" * 60)
            print(f"近似R²               : {diag['R2_Approximate']:.4f}")
            print(f"调整R² (近似)        : {diag['Adjusted_R2_Approximate']:.4f}")
            print(f"RMSE                 : {diag['RMSE']:.4f}")
            print(f"响应变量均值         : {diag['Mean_Response']:.4f}")
            print(f"观测数               : {diag['Observations']}")

            # LOF 分析结果
            lof_row = next((r for r in lof_records if r["Response"] == y), None)
            if lof_row:
                print(f"\n🔬 JMP风格拟合缺失检验:")
                print(f"拟合缺失     – DF={lof_row['DF_LackOfFit']}, SS={lof_row['SS_LackOfFit']:.6f}, MS={lof_row['MS_LackOfFit']:.6f}")
                print(f"纯误差       – DF={lof_row['DF_PureError']}, SS={lof_row['SS_PureError']:.6f}, MS={lof_row['MS_PureError']:.6f}")
                print(f"总误差       – DF={lof_row['DF_LackOfFit'] + lof_row['DF_PureError']}, SS={(lof_row['SS_LackOfFit'] + lof_row['SS_PureError']):.6f}")
                print(f"F 比值       : {lof_row['F_Ratio']:.4f}")
                print(f"p值          : {lof_row['p_Value']:.5f}")
            
            # 未编码固定效应表
            print(f"\n📄 固定效应估计 (未编码):")
            print(f"{'估计值':>12s}    {'项目'}")
            for idx, row in uncoded_df.iterrows():
                print(f"{row['Estimate']:12.6f}    {row['Factor']}")

        # === 保存结果文件 ===
        print("\n" + "="*80)
        print("💾 保存分析结果")
        print("="*80)
        
        os.makedirs(output_dir, exist_ok=True)

        # 保存固定截距
        fixed_intercepts = []
        for y in response_vars:
            beta_0 = models[y].fe_params["Intercept"]
            fixed_intercepts.append({"Response": y, "Fixed_Intercept": beta_0})

        fixed_df = pd.DataFrame(fixed_intercepts)
        fixed_df.to_csv(os.path.join(output_dir, "fixed_intercepts.csv"), index=False)

        # 保存各种结果
        effect_summary_all.to_csv(os.path.join(output_dir, "fullmodel_logworth.csv"), index=False)
        simplified_logworth_df.to_csv(os.path.join(output_dir, "simplified_logworth.csv"), index=False)
        pd.concat(param_coded_list).to_csv(os.path.join(output_dir, "coded_parameters.csv"), index=False)
        pd.concat(param_uncoded_list).to_csv(os.path.join(output_dir, "uncoded_parameters.csv"), index=False)
        
        diagnostics_df = pd.DataFrame(diagnostics_summary)
        diagnostics_df.to_csv(os.path.join(output_dir, "diagnostics_summary.csv"), index=False)
        
        pd.DataFrame(lof_records).to_csv(os.path.join(output_dir, "JMP_style_lof.csv"), index=False)
        
        # 标准化信息
        pd.DataFrame({
            "Variable": predictors,
            "Mean": scaler.mean_,
            "StdDev": scaler.scale_
        }).to_csv(os.path.join(output_dir, "scaler.csv"), index=False)

        # 模型公式
        with open(os.path.join(output_dir, "model_formulas.txt"), "w") as f:
            for y in response_vars:
                formula = f"{y} ~ " + " + ".join(simplified_factors)
                f.write(f"{y} formula:\n{formula}\n\n")

        # 残差数据
        for y in response_vars:
            try:
                model_fit = models[y]
                y_true = df[y]
                y_pred = model_fit.fittedvalues
                resid = y_true - y_pred

                rmse = np.sqrt(np.mean(resid ** 2))
                pseudo_stud_resid = resid / rmse if rmse > 0 else resid

                df_out = pd.DataFrame({
                    "Config_combo": df["Config_combo"],
                    "Actual": y_true,
                    "Predicted": y_pred,
                    "Residual": resid,
                    "Pseudo_Studentized_Residual": pseudo_stud_resid
                })
                df_out.index.name = "ID"

                out_path = os.path.join(output_dir, f"residual_data_{y}_from_MixedModel.csv")
                df_out.to_csv(out_path)

            except Exception as e:
                print(f"❌ 残差输出失败 [{y}]: {e}")

        # 设计数据和其他文件
        df_raw.to_csv(os.path.join(output_dir, "design_data.csv"), index=False)
        
        df_var = pd.DataFrame(var_records)
        df_var.to_csv(os.path.join(output_dir, "mixed_model_variance_summary.csv"), index=False)

        brief_path = os.path.join(output_dir, "InputDataBrief.csv")
        brief_df = pd.DataFrame({
            "Variable": predictors,
            "Mean (after standardization)": df[predictors].mean().values,
            "StdDev (after standardization)": df[predictors].std(ddof=0).values,
            "Original Mean (X_mean)": scaler.mean_,
            "Original StdDev (X_std)": scaler.scale_
        })
        brief_df.to_csv(brief_path, index=False)

        print(f"\n✅ 所有建模结果已基于混合模型导出为CSV，保存在：{output_dir}")
        
        # 文件列表
        saved_files = [f for f in os.listdir(output_dir) if f.endswith(('.csv', '.txt'))]
        print(f"📁 共生成 {len(saved_files)} 个结果文件:")
        for file in sorted(saved_files):
            print(f"   - {file}")

    except Exception as e:
        print(f"❌ 分析过程中发生错误: {str(e)}")
        import traceback
        tb = traceback.format_exc()
        print(f"详细错误信息:\n{tb}")
        # 关键：将异常堆栈也写入 Render 平台日志
        try:
            with open("/tmp/last_error.log", "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
    
    finally:
        # 恢复原始输出并获取捕获的文本
        sys.stdout = original_stdout
        captured_output = console_output.getvalue()
        console_output.close()
        
        # 保存控制台输出到文件
        if output_dir and os.path.exists(output_dir):
            console_output_path = os.path.join(output_dir, "console_output.txt")
            with open(console_output_path, "w", encoding="utf-8") as f:
                f.write(captured_output)
        
        # 返回控制台输出内容
        return captured_output

# 直接运行脚本时的入口
if __name__ == "__main__":
    console_output = run_mixed_model_doe_with_output(
        r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOEData_20250622.csv",
        r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOE_MixedModel_Outputs"
    )
    print("=" * 80)
    print("🖥️  VS Code终端输出 (与Web输出完全相同)")
    print("=" * 80)
    print(console_output)
