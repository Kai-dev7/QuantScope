# 可选：外部顾问式复核（External Advisory Review）

> 完全可选、默认关闭的能力：在生成最终报告之后，可调用一个**外部**的顾问式复核接口，获得一条可独立验证的建议性意见。
> 它**不是**投资建议，**不会**改变 QuantScope 自身的输出，仅作为附加注解展示。

## 定位与边界

本能力严格遵循 QuantScope 的研究 / 教育定位，不引入实盘交易，也不对分析结果做交易门控：

- **完全可选，默认关闭**：未显式开启时不产生任何外部调用。
- **仅用用户自备凭据**：通过用户自行提供的 API Key 配置，项目本身不绑定任何账号或厂商。
- **仅为顾问式注解**：复核结果只作为附加信息展示，**绝不覆盖或修改** QuantScope 的报告与建议。
- **非阻塞、可降级**：超时或出错时回退为 `review_unavailable`，不影响主流程。
- **外部第三方输出**：明确标注为外部第三方意见，**不构成投资建议**。
- **通用钩子，不绑定供应商**：通过可配置的 `EXTERNAL_REVIEW_ENDPOINT` 实现，任何兼容接口均可接入；下文以 invinoveritas 作为参考实现。

## 配置（均为 [OPTIONAL]）

在 `.env` 中按需添加（默认关闭，留空即视为未启用）：

```bash
# [OPTIONAL] 外部顾问式复核（默认关闭，完全可选）
EXTERNAL_REVIEW_ENABLED=false
# 通用复核接口地址（参考实现：invinoveritas /review）
EXTERNAL_REVIEW_ENDPOINT=https://api.babyblueviper.com/review
# 用户自备凭据（不提供则视为未配置）
EXTERNAL_REVIEW_API_KEY=
```

## 用法

在拿到最终报告（`get_final_report`）之后，将其**建议文本**传入复核接口。结果仅作注解使用：

```python
import os
import requests


def external_review(recommendation: str, stock_symbol: str = "") -> dict:
    """可选的外部顾问式复核。默认关闭，仅在用户显式配置后启用。
    始终是注解，绝不覆盖 QuantScope 自身的输出；任何失败都非阻塞降级。"""
    if os.getenv("EXTERNAL_REVIEW_ENABLED", "false").lower() != "true":
        return {"status": "disabled"}

    endpoint = os.getenv("EXTERNAL_REVIEW_ENDPOINT", "").strip()
    api_key = os.getenv("EXTERNAL_REVIEW_API_KEY", "").strip()
    if not endpoint or not api_key:
        return {"status": "review_unavailable", "reason": "not_configured"}

    try:
        resp = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                # 待复核的内容（QuantScope 的建议文本）
                "artifact": recommendation,
                # 明确这是对研究报告的顾问式复核，并非交易指令
                "context": f"Advisory review of a QuantScope research report ({stock_symbol}). "
                           f"Research/education only. Not a trade instruction.",
                # 返回一份可独立验证的签名凭据
                "sign": True,
            },
            timeout=8,
        )
        resp.raise_for_status()
        v = resp.json()
        return {
            "status": "ok",
            "verdict": v.get("verdict"),     # approve / approve_with_concerns / reject
            "summary": v.get("summary"),
            "issues": v.get("issues", []),
            "proof": v.get("proof"),         # 可独立验证，见下文
        }
    except Exception as exc:                  # 非阻塞：任何异常都降级，不影响主流程
        return {"status": "review_unavailable", "reason": type(exc).__name__}


# 在最终报告生成之后调用（结果仅作附加注解，绝不修改 report 本身）
res = get_final_report(task_id=task_id)
if res.get("found"):
    report = res["report"]
    annotation = external_review(report.get("recommendation", ""), report.get("stock_symbol", ""))
    # 将 annotation 作为“外部第三方顾问意见”展示，与 QuantScope 自身输出并列、互不覆盖
```

## 独立验证（无需信任复核方）

返回的 `proof` 是一份可重新计算的签名凭据。任何人都可以用**免费、免鉴权**的接口独立验证它，从而不必信任复核方本身：

```bash
curl -s -X POST https://api.babyblueviper.com/verify-proof \
  -H "Content-Type: application/json" \
  -d '{"proof": <上面返回的 proof 对象>}'
```

这也是该参考实现的设计取向：结论可由公开数据重新推导，不依赖可信硬件，也不依赖可信评分方。

## 参考实现

- 接口为通用钩子，`EXTERNAL_REVIEW_ENDPOINT` 可指向任何兼容服务；本文以 invinoveritas（`api.babyblueviper.com`）作为参考实现。
- 该服务按调用计费，使用用户自备凭据；QuantScope 不绑定、不代管任何账号。

---

> **Maintainer note (EN).** This is docs-only and follows every boundary from the issue: fully opt-in and
> disabled by default; configured only through user-provided credentials; advisory annotation only, never
> an override of QuantScope's output; non-blocking with a `review_unavailable` timeout/error fallback;
> clearly documented as external third-party output and not financial advice; and implemented through a
> generic `EXTERNAL_REVIEW_ENDPOINT` hook rather than coupling the core project to one vendor. No change to
> QuantScope's analysis pipeline or its research/report positioning.
