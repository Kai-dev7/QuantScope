"""Email report rendering and delivery service."""
from __future__ import annotations

import html
import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger(__name__)


def _get_env_alias(keys: list[str], default: str = "") -> str:
    for key in keys:
        value = os.getenv(key)
        if value is not None:
            return value
    return default


def _clip(text: str | None, limit: int = 1000) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())[:limit]


def _escape(text: str | None) -> str:
    return html.escape(str(text or ""))


def _build_html(report: dict) -> str:
    symbol = _escape(report.get("stock_symbol") or report.get("symbol"))
    name = _escape(report.get("stock_name") or "")
    trade_date = _escape(report.get("analysis_date") or report.get("created_at") or "")
    decision = _escape(report.get("decision") or report.get("recommendation") or "-")
    summary = _escape(_clip(report.get("summary") or report.get("final_trade_decision") or report.get("analysis_summary")))
    return f"""
    <html>
      <body style="font-family:Arial,sans-serif;background:#f6f7fb;padding:24px;">
        <div style="max-width:720px;margin:0 auto;background:#fff;border-radius:12px;padding:24px;">
          <h2 style="margin:0 0 12px;">TradingAgents 定时分析报告</h2>
          <p><b>标的：</b>{name or symbol}</p>
          <p><b>代码：</b>{symbol}</p>
          <p><b>日期：</b>{trade_date}</p>
          <p><b>结论：</b>{decision}</p>
          <hr />
          <p style="white-space:pre-wrap;line-height:1.7;">{summary}</p>
        </div>
      </body>
    </html>
    """


def send_report_email(user, report: dict) -> bool:
    smtp_host = _get_env_alias(["MAIL_HOST", "MAIL_SERVER", "SMTP_HOST"]).strip()
    if not smtp_host:
        logger.info("[email_report] SMTP not configured, skipping send for %s", getattr(user, "email", "unknown"))
        return False

    smtp_port = int(_get_env_alias(["MAIL_PORT", "SMTP_PORT"], "587"))
    smtp_user = _get_env_alias(["MAIL_USER", "MAIL_USERNAME", "SMTP_USER"]).strip()
    smtp_password = _get_env_alias(["MAIL_PASS", "MAIL_PASSWORD", "SMTP_PASSWORD"]).strip()
    smtp_from = _get_env_alias(["MAIL_FROM", "SMTP_FROM"], smtp_user or "noreply@example.com").strip()
    smtp_starttls = _get_env_alias(["MAIL_STARTTLS", "SMTP_TLS"], "1").strip().lower() not in ("0", "false", "no", "off")
    smtp_ssl = _get_env_alias(["MAIL_SSL", "MAIL_SSL_TLS"], "0").strip().lower() in ("1", "true", "yes", "on")

    msg = EmailMessage()
    msg["Subject"] = f"TradingAgents 定时分析报告 - {report.get('stock_symbol') or report.get('symbol')}"
    msg["From"] = smtp_from
    msg["To"] = getattr(user, "email", "")
    msg.set_content(
        f"TradingAgents 定时分析完成\n"
        f"标的: {report.get('stock_symbol') or report.get('symbol')}\n"
        f"结论: {report.get('decision') or report.get('recommendation') or '-'}\n"
    )
    msg.add_alternative(_build_html(report), subtype="html")

    smtp_cls = smtplib.SMTP_SSL if smtp_ssl else smtplib.SMTP
    with smtp_cls(smtp_host, smtp_port, timeout=20) as server:
        if smtp_starttls and not smtp_ssl:
            server.starttls()
        if smtp_user:
            server.login(smtp_user, smtp_password)
        server.send_message(msg)
    logger.info("[email_report] sent OK to %s", getattr(user, "email", "unknown"))
    return True


async def send_report_email_with_retry(user, report: dict) -> bool:
    try:
        return await asyncio.to_thread(send_report_email, user, report)
    except Exception as exc:
        logger.warning("[email_report] first attempt failed for %s: %s", getattr(user, "email", "unknown"), exc)
        return False
