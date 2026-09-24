#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
resume.py —— 简历技能统一入口（多人母版）

本技能可同时维护多个人的母版，每人一个目录：

    people/
      _template/            模板（复制用，不改动）
        master.template.yaml
        tailored.template.yaml
      张三/
        master.yaml         母版（唯一事实源）
        master.preview.md   只读预览（自动生成，勿手改）
        sources/            原始材料存档（只追加，永不修改）
        targets/            按岗位定制
          <公司>-<岗位>/
            jd.txt
            tailored.yaml
        output/             出片产物

用法（在含 people/ 的工作区目录执行；<RT> = resume-tailor/scripts）：

    python <RT>/resume.py init                      # 新装后先跑：建 people/ 并放模板
    python <RT>/resume.py people                    # 列出所有人
    python <RT>/resume.py new     --person 张三      # 建母版
    python <RT>/resume.py check   --person 张三
    python <RT>/resume.py lint    --person 张三
    python <RT>/resume.py preview --person 张三
    python <RT>/resume.py render  --person 张三 [--mode draft|final]

路径：包根（config/ assets/ scripts/）按脚本自身位置自解析，可整体拷走；
      people/ 从当前工作目录找，也可用环境变量 RESUME_WORKSPACE 指定。
--person 可省略：当 people/ 下只有一个人时自动选中。
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # 包根：config/ assets/ references/ scripts/
WORKSPACE = Path(os.environ.get("RESUME_WORKSPACE") or Path.cwd())  # 工作区：people/ 所在目录
PEOPLE = WORKSPACE / "people"
PY = sys.executable


def list_people():
    if not PEOPLE.exists():
        return []
    return sorted(
        d for d in PEOPLE.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )


def resolve_person(name=None):
    people = list_people()
    if not people:
        sys.exit("people/ 下还没有任何人。先运行：python scripts/resume.py new --person 姓名")
    if name:
        hit = [p for p in people if p.name == name]
        if not hit:
            sys.exit(f"找不到「{name}」。现有：{', '.join(p.name for p in people)}")
        return hit[0]
    if len(people) > 1:
        sys.exit(
            f"people/ 下有多人（{', '.join(p.name for p in people)}），"
            "请用 --person 指定。"
        )
    return people[0]


def run(args_):
    return subprocess.run([PY] + args_, cwd=str(WORKSPACE)).returncode


def main():
    ap = argparse.ArgumentParser(description="简历技能统一入口")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("people", help="列出所有已维护的人")
    sub.add_parser("init", help="在当前工作区初始化 people/ 并放入模板（新装后先跑一次）")

    p_new = sub.add_parser("new", help="为新人创建母版（从模板复制）")
    p_new.add_argument("--person", required=True)

    for name, help_ in [
        ("check", "校验母版（Gate G1/G2/G4 机械部分）"),
        ("lint", "只扫中文 AI 味词表"),
        ("preview", "生成 Markdown 只读预览"),
        ("render", "出片：渲染 HTML 简历"),
    ]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("--person", default=None)
        if name == "render":
            p.add_argument("--mode", default="draft", choices=["draft", "final"])
            p.add_argument("--target", default=None, help="定制版 yaml 路径（相对该人目录）")
        if name == "preview":
            p.add_argument("-o", "--out", default=None)

    args = ap.parse_args()

    if args.cmd == "people":
        people = list_people()
        if not people:
            print("people/ 下还没有任何人。")
            return 0
        print(f"已维护 {len(people)} 人：")
        for p in people:
            m = p / "master.yaml"
            v = "?"
            if m.exists():
                for line in m.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.strip().startswith("version:"):
                        v = line.split(":", 1)[1].strip()
                        break
            tgt = len([d for d in (p / "targets").iterdir() if d.is_dir()]) if (p / "targets").exists() else 0
            print(f"  {p.name:<12} 母版 v{v:<4} 定制版 {tgt} 个")
        return 0

    if args.cmd == "init":
        # 初始化工作区：建 people/，并把包内 assets/ 的模板落进 people/_template/
        PEOPLE.mkdir(parents=True, exist_ok=True)
        tdir = PEOPLE / "_template"
        tdir.mkdir(parents=True, exist_ok=True)
        n = 0
        for src, dstname in (
            (ROOT / "assets" / "master.template.yaml", "master.template.yaml"),
            (ROOT / "assets" / "tailored.template.yaml", "tailored.template.yaml"),
        ):
            if src.exists():
                (tdir / dstname).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                n += 1
        print(f"[OK] 工作区已初始化：{PEOPLE}")
        print(f"     已放置模板 {n} 份 -> {tdir}")
        print("下一步：python <包路径>/scripts/resume.py new --person 姓名")
        return 0

    if args.cmd == "new":
        dest = PEOPLE / args.person
        if dest.exists():
            sys.exit(f"「{args.person}」已存在：{dest}")
        for sub_ in ("sources", "output", "targets"):
            (dest / sub_).mkdir(parents=True, exist_ok=True)
        # 模板查找顺序：工作区 people/_template/ → 包内 assets/
        # 后者保证「刚装好、工作区还是空的」的新用户也能建出带字段的母版。
        tpl = PEOPLE / "_template" / "master.template.yaml"
        if not tpl.exists():
            tpl = ROOT / "assets" / "master.template.yaml"
        if tpl.exists():
            (dest / "master.yaml").write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            print(f"[WARN] 未找到母版模板（已查 {PEOPLE / '_template'} 与 {ROOT / 'assets'}），"
                  "只建了目录，请自行放入 master.yaml")
        print(f"已创建：{dest.relative_to(WORKSPACE)}")
        print(f"下一步：把原始材料放进 {dest / 'sources'}，然后运行")
        print(f"        python <包路径>/scripts/resume.py check --person {args.person}")
        return 0

    person = resolve_person(args.person)
    master = person / "master.yaml"

    if args.cmd == "check":
        return run([str(ROOT / "scripts" / "validate_master.py"), "check", str(master.relative_to(WORKSPACE))])

    if args.cmd == "lint":
        return run([str(ROOT / "scripts" / "validate_master.py"), "lint", str(master.relative_to(WORKSPACE))])

    if args.cmd == "preview":
        out = args.out or str((person / "master.preview.md").relative_to(WORKSPACE))
        return run([
            str(ROOT / "scripts" / "validate_master.py"), "preview",
            str(master.relative_to(WORKSPACE)), "-o", out,
        ])

    if args.cmd == "render":
        if args.target:
            # 用定制版所在目录名命名，避免多个定制版互相覆盖
            tname = Path(args.target).parent.name or "custom"
            out = person / "output" / f"resume-{tname}-{args.mode}.html"
        else:
            out = person / "output" / f"resume-{args.mode}.html"
        cmd = [
            str(ROOT / "scripts" / "render_resume.py"),
            str(master.relative_to(WORKSPACE)),
            "-o", str(out.relative_to(WORKSPACE)),
            "--mode", args.mode,
        ]
        if args.target:
            cmd += ["--target", str((person / args.target).relative_to(WORKSPACE))]
        return run(cmd)

    return 1


if __name__ == "__main__":
    sys.exit(main())
