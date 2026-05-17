"""Email report rendering and delivery service for QuantScope.

Renders analysis reports as HTML emails and sends them via SMTP.
"""
from __future__ import annotations

import asyncio
import html
import logging
import os
import re
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

import markdown as _md

logger = logging.getLogger("app.services.email_report_service")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_env_alias(keys: list[str], default: str = "") -> str:
    """Return the first non-None env var from *keys*, else *default*."""
    for k in keys:
        v = os.getenv(k)
        if v is not None:
            return v
    return default


def _escape(text: str) -> str:
    """HTML-escape user-supplied text."""
    return html.escape(str(text))


def _render_markdown(text: str) -> str:
    """Convert markdown to HTML with inline styles for email clients."""
    raw = _md.markdown(text, extensions=["tables"])
    raw = raw.replace("<table>",
        '<table style="width:100%;border-collapse:collapse;font-size:13px;margin:12px 0;">')
    raw = raw.replace("<thead>",
        '<thead style="background:#e0f2fe;">')
    raw = raw.replace("<th>",
        '<th style="text-align:left;padding:8px 12px;border:1px solid #cbd5e1;font-weight:600;color:#0f172a;">')
    raw = raw.replace("<td>",
        '<td style="padding:8px 12px;border:1px solid #e2e8f0;color:#334155;">')
    raw = raw.replace("<h3>",
        '<h3 style="font-size:14px;font-weight:700;color:#0f172a;margin:16px 0 8px;">')
    raw = raw.replace("<h4>",
        '<h4 style="font-size:13px;font-weight:700;color:#1e293b;margin:14px 0 6px;">')
    raw = raw.replace("<strong>",
        '<strong style="font-weight:700;color:#0f172a;">')
    raw = raw.replace("<hr>",
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;">')
    raw = raw.replace("<hr />",
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;">')
    raw = raw.replace("<ol>",
        '<ol style="margin:8px 0;padding-left:20px;color:#334155;">')
    raw = raw.replace("<ul>",
        '<ul style="margin:8px 0;padding-left:20px;color:#334155;">')
    raw = raw.replace("<li>",
        '<li style="margin:4px 0;">')
    raw = raw.replace("<blockquote>",
        '<blockquote style="margin:12px 0;padding:10px 16px;border-left:3px solid #3b82f6;background:#f8fafc;color:#475569;">')
    return raw


def _infer_frontend_url() -> str:
    """Infer frontend URL from FRONTEND_URL or CORS_ALLOW_ORIGINS."""
    explicit = os.getenv("FRONTEND_URL", "").strip()
    if explicit:
        return explicit
    raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if not raw:
        return ""
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    for o in origins:
        if "localhost" not in o and "127.0.0.1" not in o:
            return o
    return origins[0] if origins else ""


_VERDICT_RE = re.compile(r"<!--\s*VERDICT:\s*(\{[^>]+\})\s*-->")
_DIRECTION_ALIAS = {
    "BULLISH": "看多",
    "LEAN_BULLISH": "偏多",
    "BEARISH": "看空",
    "LEAN_BEARISH": "偏空",
    "NEUTRAL": "中性",
    "CAUTIOUS": "谨慎",
}


def _extract_verdict(text: str) -> Optional[dict]:
    """Extract structured verdict from agent report HTML comment."""
    m = _VERDICT_RE.search(text)
    if not m:
        return None
    try:
        parsed = eval(m.group(1))  # Safe: we control the regex pattern
        direction = parsed.get("direction", "")
        reason = parsed.get("reason", "")
        if not direction or not reason:
            return None
        direction = _DIRECTION_ALIAS.get(direction.upper(), direction)
        return {"direction": direction, "reason": reason.strip()[:42]}
    except (ValueError, SyntaxError):
        return None


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_DIRECTION_COLOR = {
    "看多": "#16a34a",
    "偏多": "#65a30d",
    "多": "#16a34a",
    "看空": "#dc2626",
    "偏空": "#ea580c",
    "空": "#dc2626",
    "中性": "#9ca3af",
    "谨慎": "#f59e0b",
}

_RISK_LEVEL_COLORS = {
    "high": "#dc2626",
    "medium": "#f59e0b",
    "low": "#16a34a",
}

_KEY_METRIC_STATUS_COLORS = {
    "good": "#16a34a",
    "neutral": "#6b7280",
    "bad": "#dc2626",
}

_AGENT_SECTIONS = [
    ("market_report", "市场分析"),
    ("sentiment_report", "舆情分析"),
    ("news_report", "新闻分析"),
    ("fundamentals_report", "基本面分析"),
    ("macro_report", "宏观分析"),
    ("smart_money_report", "主力资金分析"),
    ("volume_price_report", "量价分析"),
]


def render_report_html(
    stock_code: str,
    stock_name: str,
    trade_date: str,
    decision: dict,
    direction: str,
    confidence: Optional[float],
    target_price: Optional[float],
    stop_loss: Optional[float],
    state: Dict[str, Any],
    frontend_url: str = "",
) -> str:
    """Render analysis result as an HTML email string with inline CSS."""

    name = _escape(stock_name) if stock_name and stock_name != stock_code else ""
    symbol = _escape(stock_code or "")
    direction_color = _DIRECTION_COLOR.get(direction, "#6b7280")
    direction_bg = {
        "看多": "#dcfce7", "偏多": "#ecfccb", "多": "#dcfce7",
        "看空": "#fee2e2", "偏空": "#ffedd5", "空": "#fee2e2",
        "中性": "#f3f4f6", "谨慎": "#fef3c7",
    }.get(direction, "#f3f4f6")

    conf_str = f"{confidence:.0f}%" if confidence is not None else "-"
    conf_width = confidence if confidence is not None else 0

    # Action display (Buy/Sell/Hold)
    action = decision.get("action", "-") if isinstance(decision, dict) else "-"

    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>',
        '<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,\'Helvetica Neue\',Arial,sans-serif;-webkit-font-smoothing:antialiased;">',
        '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;">',
        '<tr><td align="center" style="padding:32px 16px;">',
        '<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">',
    ]

    # Header with gradient
    parts.append(
        '<tr><td style="background:#0f172a;padding:28px 32px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td><p style="margin:0;font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.3px;">QuantScope 智能投研报告</p>'
        f'<p style="margin:6px 0 0;font-size:14px;color:#94a3b8;">{name + " " if name else ""}{symbol} &middot; {trade_date}</p></td>'
        f'<td align="right" valign="top">'
        f'<span style="display:inline-block;background:{direction_bg};color:{direction_color};font-size:15px;font-weight:700;padding:6px 16px;border-radius:20px;">{_escape(direction) or "-"}</span>'
        f'</td></tr></table>'
        '</td></tr>'
    )

    # Decision card: 3-column summary
    parts.append('<tr><td style="padding:24px 32px 0;">')
    parts.append('<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;">')
    parts.append('<tr>')

    # Decision column
    parts.append(
        '<td width="33%" style="padding:16px;background:#f8fafc;border-radius:12px;text-align:center;border:1px solid #e2e8f0;">'
        f'<p style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#64748b;">决策</p>'
        f'<p style="margin:8px 0 0;font-size:24px;font-weight:800;color:#0f172a;">{_escape(action)}</p>'
        '</td>'
    )
    parts.append('<td width="2%"></td>')

    # Confidence column with progress bar
    parts.append(
        '<td width="32%" style="padding:16px;background:#f8fafc;border-radius:12px;text-align:center;border:1px solid #e2e8f0;">'
        f'<p style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#64748b;">置信度</p>'
        f'<p style="margin:8px 0 6px;font-size:24px;font-weight:800;color:#0f172a;">{conf_str}</p>'
        f'<div style="background:#e2e8f0;border-radius:4px;height:6px;overflow:hidden;">'
        f'<div style="background:linear-gradient(90deg,#3b82f6,#06b6d4);width:{conf_width}%;height:6px;border-radius:4px;"></div>'
        f'</div>'
        '</td>'
    )
    parts.append('<td width="2%"></td>')

    # Direction column
    parts.append(
        '<td width="33%" style="padding:16px;background:#f8fafc;border-radius:12px;text-align:center;border:1px solid #e2e8f0;">'
        f'<p style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#64748b;">方向</p>'
        f'<p style="margin:8px 0 0;font-size:24px;font-weight:800;color:{direction_color};">{_escape(direction) or "-"}</p>'
        '</td>'
    )

    parts.append('</tr></table>')
    parts.append('</td></tr>')

    # Target / stop-loss price boxes
    if target_price is not None or stop_loss is not None:
        parts.append('<tr><td style="padding:12px 32px 0;">')
        parts.append('<table width="100%" cellpadding="0" cellspacing="0"><tr>')
        if target_price is not None:
            parts.append(
                f'<td width="49%" style="background:#fef2f2;border-radius:10px;padding:14px 16px;border:1px solid #fecaca;">'
                f'<p style="margin:0;font-size:11px;color:#991b1b;text-transform:uppercase;letter-spacing:0.5px;">&#127919; 目标价</p>'
                f'<p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#dc2626;">¥{target_price:.2f}</p>'
                f'</td>'
            )
            parts.append('<td width="2%"></td>')
        if stop_loss is not None:
            parts.append(
                f'<td width="49%" style="background:#f0fdf4;border-radius:10px;padding:14px 16px;border:1px solid #bbf7d0;">'
                f'<p style="margin:0;font-size:11px;color:#166534;text-transform:uppercase;letter-spacing:0.5px;">&#128737; 止损价</p>'
                f'<p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#16a34a;">¥{stop_loss:.2f}</p>'
                f'</td>'
            )
        parts.append('</tr></table></td></tr>')

    # Agent verdicts
    verdicts: list[tuple[str, dict]] = []
    for attr, title in _AGENT_SECTIONS:
        content = state.get(attr, None)
        if content is None:
            continue
        verdict = _extract_verdict(content) if isinstance(content, str) else None
        if verdict:
            verdicts.append((title, verdict))

    if verdicts:
        parts.append('<tr><td style="padding:24px 32px 0;">')
        parts.append('<p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#0f172a;">&#128101; 各方观点</p>')
        for i, (title, v) in enumerate(verdicts):
            d_color = _DIRECTION_COLOR.get(v["direction"], "#6b7280")
            d_bg = {
                "看多": "#dcfce7", "偏多": "#ecfccb", "多": "#dcfce7",
                "看空": "#fee2e2", "偏空": "#ffedd5", "空": "#fee2e2",
                "中性": "#f3f4f6", "谨慎": "#fef3c7",
            }.get(v["direction"], "#f3f4f6")
            border_bottom = "border-bottom:1px solid #f1f5f9;" if i < len(verdicts) - 1 else ""
            parts.append(
                f'<table width="100%" cellpadding="0" cellspacing="0" style="{border_bottom}">'
                f'<tr><td style="padding:10px 0;">'
                f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td style="width:110px;font-size:13px;color:#64748b;font-weight:500;">{title}</td>'
                f'<td style="width:60px;"><span style="display:inline-block;background:{d_bg};color:{d_color};font-size:12px;font-weight:700;padding:3px 10px;border-radius:12px;">{_escape(v["direction"])}</span></td>'
                f'<td style="font-size:13px;color:#475569;padding-left:8px;">{_escape(v["reason"])}</td>'
                f'</tr></table>'
                f'</td></tr></table>'
            )
        parts.append('</td></tr>')

    # Final trade decision
    final_trade_decision = state.get("final_trade_decision") or state.get("investment_plan")
    if final_trade_decision:
        ftd_html = _render_markdown(final_trade_decision) if isinstance(final_trade_decision, str) else str(final_trade_decision)
        parts.append(
            '<tr><td style="padding:24px 32px 0;">'
            '<p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#0f172a;">&#128221; 最终交易决策</p>'
            f'<div style="font-size:13px;color:#334155;line-height:1.7;background:#f0f9ff;padding:16px 20px;border-radius:10px;border-left:4px solid #3b82f6;">{ftd_html}</div>'
            '</td></tr>'
        )

    # View full report button
    if frontend_url:
        report_url = f"{frontend_url.rstrip('/')}/reports?symbol={stock_code}"
        parts.append(
            '<tr><td style="padding:28px 32px 0;" align="center">'
            f'<a href="{_escape(report_url)}" target="_blank" style="'
            'display:inline-block;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:#ffffff;'
            'font-size:14px;font-weight:700;padding:12px 36px;'
            'border-radius:10px;text-decoration:none;letter-spacing:0.3px;">'
            '&#128196; 查看完整报告</a>'
            '</td></tr>'
        )

    # Footer
    parts.append(
        '<tr><td style="padding:28px 32px;border-top:1px solid #e2e8f0;margin-top:24px;text-align:center;">'
        '<p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;">本报告由 QuantScope 多智能体系统自动生成，仅供参考，不构成投资建议。</p>'
        '<p style="margin:10px 0 0;font-size:12px;color:#94a3b8;">觉得有帮助？请在 GitHub 上给我们点个 &#11088; Star</p>'
        f'<p style="margin:12px 0 0;font-size:11px;color:#cbd5e1;">不想收到此邮件？请登录后在「设置」页面关闭「邮件报告推送」即可取消订阅。</p>'
        '</td></tr>'
    )
    parts.append('</table></td></tr></table></body></html>')

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SMTP sending
# ---------------------------------------------------------------------------

def send_report_email(
    user_email: str,
    user_id: str,
    stock_code: str,
    stock_name: str,
    trade_date: str,
    decision: dict,
    direction: str,
    confidence: Optional[float],
    target_price: Optional[float],
    stop_loss: Optional[float],
    state: Dict[str, Any],
) -> bool:
    """Send the rendered report email via SMTP.

    Returns True on success, False on failure. Never raises.
    """
    smtp_host = _get_env_alias(["MAIL_HOST", "MAIL_SERVER", "SMTP_HOST"]).strip()
    if not smtp_host:
        logger.info("[email_report] SMTP not configured, skipping send")
        return False

    smtp_port = int(_get_env_alias(["MAIL_PORT", "SMTP_PORT"]) or "587")
    smtp_user = _get_env_alias(["MAIL_USER", "MAIL_USERNAME", "SMTP_USER"]).strip()
    smtp_password = _get_env_alias(["MAIL_PASS", "MAIL_PASSWORD", "SMTP_PASSWORD"]).strip()
    smtp_from = _get_env_alias(["MAIL_FROM", "SMTP_FROM"], smtp_user or "noreply@example.com").strip()

    smtp_starttls_str = _get_env_alias(["MAIL_STARTTLS", "SMTP_TLS"], "1").strip().lower()
    smtp_starttls = smtp_starttls_str not in ("0", "false", "off", "no")

    smtp_ssl_tls_str = _get_env_alias(["MAIL_SSL", "MAIL_SSL_TLS"], "0").strip().lower()
    smtp_ssl_tls = smtp_ssl_tls_str in ("1", "true", "on", "yes")

    frontend_url = _infer_frontend_url()
    html_body = render_report_html(
        stock_code=stock_code,
        stock_name=stock_name,
        trade_date=trade_date,
        decision=decision,
        direction=direction,
        confidence=confidence,
        target_price=target_price,
        stop_loss=stop_loss,
        state=state,
        frontend_url=frontend_url,
    )

    display_name = f"{stock_name} {stock_code}" if stock_name and stock_name != stock_code else stock_code

    report_link = ""
    if frontend_url:
        report_link = f"\n\n查看完整报告: {frontend_url.rstrip('/')}/reports?symbol={stock_code}"

    action = decision.get("action", "-") if isinstance(decision, dict) else "-"
    msg = EmailMessage()
    msg["Subject"] = f"QuantScope 投研报告 - {display_name} ({trade_date})"
    msg["From"] = smtp_from
    msg["To"] = user_email

    confidence_str = f"{confidence:.0f}%" if confidence is not None else "-"
    plain = (
        f"QuantScope 投研报告\n{display_name} {trade_date}\n"
        f"决策: {action}\n方向: {direction or '-'}\n置信度: {confidence_str}\n{report_link}\n\n"
        "请使用支持 HTML 的邮件客户端查看完整报告。"
    )
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype="html")

    try:
        logger.info(f"[email_report] sending to {user_email} via {smtp_host}:{smtp_port}")
        smtp_cls = smtplib.SMTP_SSL if smtp_ssl_tls else smtplib.SMTP
        with smtp_cls(smtp_host, smtp_port, timeout=20) as server:
            if smtp_starttls and not smtp_ssl_tls:
                server.starttls()
            if smtp_user:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info(f"[email_report] sent OK to {user_email}")
        return True
    except Exception as e:
        logger.error(f"[email_report] failed to send to {user_email}: {e}")
        return False


# ---------------------------------------------------------------------------
# Async wrapper with retry
# ---------------------------------------------------------------------------

async def send_report_email_with_retry(
    user_email: str,
    user_id: str,
    stock_code: str,
    stock_name: str,
    trade_date: str,
    decision: dict,
    direction: str,
    confidence: Optional[float],
    target_price: Optional[float],
    stop_loss: Optional[float],
    state: Dict[str, Any],
) -> bool:
    """Send report email asynchronously, retrying once on failure after 180 s."""
    ok = await asyncio.to_thread(
        send_report_email,
        user_email, user_id, stock_code, stock_name, trade_date,
        decision, direction, confidence, target_price, stop_loss, state,
    )
    if ok:
        logger.info(f"[email_report] first attempt succeeded for {user_email}")
        return True

    logger.warning(f"[email_report] first attempt failed for {user_email}, retrying in 180s")
    await asyncio.sleep(180)
    ok = await asyncio.to_thread(
        send_report_email,
        user_email, user_id, stock_code, stock_name, trade_date,
        decision, direction, confidence, target_price, stop_loss, state,
    )
    if ok:
        logger.info(f"[email_report] retry succeeded for {user_email}")
    else:
        logger.error(f"[email_report] retry also failed for {user_email}")
    return ok