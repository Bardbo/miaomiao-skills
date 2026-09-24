#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导出 PDF：把 render 产物 HTML 经真实浏览器打印成带文字层的 .pdf（ATS 可解析）。

与 export_docx.py 同款 CLI；实际打印由 scripts/export_pdf.js（node playwright + 已装 chromium）完成，
本脚本只负责解析参数、定位 HTML、找到 node 与 node_modules 后调用它。

用法:
    python scripts/export_pdf.py --person 张三
    python scripts/export_pdf.py --person 张三 --target targets/方向A-技术向/tailored.yaml --mode draft
    python scripts/export_pdf.py --html people/张三/output/resume-final.html

前置：隔离工作区已装 node playwright + chromium（见 measure_pages.js / density.py --measure）。
"""
import argparse
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 包根：config/
WORKSPACE = os.environ.get("RESUME_WORKSPACE") or os.getcwd()        # 工作区：people/ 所在目录
PEOPLE = os.path.join(WORKSPACE, "people")


def _find_node():
    env = os.environ.get("NODE_BIN", "")
    if env and os.path.exists(env):
        return env
    home = os.path.expanduser("~")
    # 不要写死版本号（22.22.2-2 → -3 这种小版本漂移会让这里静默回落到系统 node）。
    # 直接扫托管运行时目录，取版本号最大的一个。
    vroot = os.path.join(home, ".workbuddy", "binaries", "node", "versions")
    cands = []
    if os.path.isdir(vroot):
        for d in sorted(os.listdir(vroot), reverse=True):
            cands.append(os.path.join(vroot, d, "node.exe"))
            cands.append(os.path.join(vroot, d, "bin", "node"))
    cands.append("node")
    for cand in cands:
        if os.path.exists(cand):
            return cand
    return None


def _find_node_modules():
    env = os.environ.get("NODE_PATH", "")
    if env and os.path.isdir(env):
        return env
    home = os.path.expanduser("~")
    for p in (
        os.path.join(home, ".workbuddy", "binaries", "node", "workspace", "node_modules"),
        os.path.join(home, ".workbuddy", "node", "node_modules"),
        os.path.join(ROOT, "node_modules"),
    ):
        if os.path.isdir(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--person", help="people/ 下的姓名")
    ap.add_argument("--mode", default="final", choices=["draft", "final"])
    ap.add_argument("--target", default=None, help="定制版 yaml（相对该人目录）")
    ap.add_argument("--html", default=None, help="直接指定 HTML 文件")
    ap.add_argument("--out", default=None, help="输出 .pdf 路径")
    args = ap.parse_args()

    if args.html:
        html_path = args.html
    elif args.person:
        if args.target:
            tname = os.path.basename(os.path.dirname(args.target)) or "custom"
            html_path = os.path.join(PEOPLE, args.person, "output",
                                     "resume-%s-%s.html" % (tname, args.mode))
        else:
            html_path = os.path.join(PEOPLE, args.person, "output",
                                     "resume-%s.html" % args.mode)
    else:
        ap.error("需要 --html 或 --person")

    if not os.path.exists(html_path):
        sys.exit("找不到成稿 HTML：%s\n先跑：python scripts/resume.py render --person <姓名> [--target <定制版>] --mode %s"
                 % (html_path, args.mode))

    out_path = args.out or re.sub(r"\.html$", ".pdf", html_path)

    node = _find_node()
    if not node:
        sys.exit("找不到 node 解释器（可设 NODE_BIN 环境变量指定）")
    node_modules = _find_node_modules()
    if not node_modules:
        sys.exit("找不到 node_modules（playwright 未安装？隔离工作区应已装）")

    js = os.path.join(ROOT, "scripts", "export_pdf.js")
    env = os.environ.copy()
    env["NODE_PATH"] = node_modules

    # export_pdf.js 接收 HTML，并把 PDF 写到与 HTML 同目录同名 .pdf（或 --out）
    cmd = [node, js, html_path]
    if args.out:
        cmd += ["--out", args.out]
    try:
        r = subprocess.run(cmd, capture_output=True, env=env, timeout=240)
    except subprocess.TimeoutExpired:
        sys.exit("PDF 导出超时（浏览器打印卡住？）")

    sys.stdout.write(r.stdout.decode("utf-8", "replace"))
    if r.stderr:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
    if r.returncode != 0:
        sys.exit("\nPDF 导出失败（退出码 %d）" % r.returncode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
