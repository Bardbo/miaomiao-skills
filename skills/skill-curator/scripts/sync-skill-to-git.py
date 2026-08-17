#!/usr/bin/env python3
"""
sync-skill-to-git.py -- 同步 Hermes skill 到 Git 项目目录

用法:
  python3 scripts/sync-skill-to-git.py skill-curator
  python3 scripts/sync-skill-to-git.py skill-curator --push  # 自动推送

行为:
1. 找到 Hermes skill 目录
2. 找到对应的 Git 项目目录（通过 HERMES_SKILL_BASE / GIT_PROJECT_BASE 环境变量配置）
3. 把 Git 项目目录中不属于 skill 的文件（如 README.md）备份
4. 用 skill 目录内容覆盖 Git 项目目录
5. 恢复 README.md/README_EN.md（如果 skill 里没有的话）
6. 自动 git add/commit/push
"""

import argparse
import os
import shutil
import subprocess
import sys


def run(cmd, cwd=None):
    # Windows: explicit utf-8 encoding to avoid UnicodeDecodeError on Chinese git output
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def find_skill(skill_name):
    """找到 Hermes skill 的完整路径"""
    skill_base = os.environ.get(
        "HERMES_SKILL_BASE",
        os.path.expanduser("~/.hermes/skills")
    )
    # 查找所有可能位置
    candidates = []
    for root, dirs, files in os.walk(skill_base):
        if "SKILL.md" in files:
            # 检查文件夹名是否匹配
            parent = os.path.basename(root)
            if parent == skill_name:
                candidates.append(root)
    if not candidates:
        print(f"??? 找不到 skill: {skill_name}")
        print(f"    设置 HERMES_SKILL_BASE 环境变量指定 skill 根目录")
        sys.exit(1)
    if len(candidates) > 1:
        print(f"???  找到多个同名 skill:")
        for c in candidates:
            print(f"    {c}")
        # 优先选择非子目录的
        for c in candidates:
            if skill_base in c and "/openclaw-imports/" not in c:
                return c
        return candidates[0]
    return candidates[0]


def find_git_repo(skill_name):
    """找到对应的 Git 项目目录"""
    git_base = os.environ.get(
        "GIT_PROJECT_BASE",
        os.path.expanduser("~/projects")
    )
    repo_path = os.path.join(git_base, skill_name)
    if os.path.isdir(repo_path) and os.path.isdir(os.path.join(repo_path, ".git")):
        return repo_path
    print(f"??? 找不到 Git 项目: {repo_path}")
    print(f"   设置 GIT_PROJECT_BASE 环境变量指定 Git 项目根目录")
    sys.exit(1)


def sync(skill_name, push=False):
    skill_dir = find_skill(skill_name)
    git_dir = find_git_repo(skill_name)

    print(f"? Skill 目录: {skill_dir}")
    print(f"? Git 项目: {git_dir}")

    # Step 1: 备份 README（如果 skill 里没有的话，需要从 git 历史恢复）
    readme_files = []
    for f in ["README.md", "README_EN.md"]:
        if not os.path.exists(os.path.join(skill_dir, f)):
            # 从 git 获取
            _, stdout, _ = run(f'git show HEAD:{f}', cwd=git_dir)
            if stdout:
                readme_files.append(f)

    # Step 2: 清理 git 项目中的非 .git 文件
    for item in os.listdir(git_dir):
        if item == ".git":
            continue
        path = os.path.join(git_dir, item)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    # Step 3: 从 skill 目录复制
    for item in os.listdir(skill_dir):
        src = os.path.join(skill_dir, item)
        dst = os.path.join(git_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Step 4: 恢复 README（如果 skill 里没有）
    for f in readme_files:
        _, stdout, _ = run(f'git show HEAD:{f}', cwd=git_dir)
        if stdout:
            with open(os.path.join(git_dir, f), "w", encoding="utf-8") as fw:
                fw.write(stdout)

    # Step 5: git add/commit/push
    _, stdout, stderr = run("git add -A", cwd=git_dir)
    _, status_out, _ = run("git status --porcelain", cwd=git_dir)
    if not status_out:
        print("??? 没有变化，无需提交")
        return

    _, stdout, _ = run("git diff --cached --stat", cwd=git_dir)
    print(f"\n??? 变更统计:\n{stdout}")

    _, _, _ = run('git commit -m "sync: update from Hermes skill"', cwd=git_dir)
    print("??? 已 commit")

    if push:
        # 使用 git -c 语法（跨 shell 兼容），避免 bash env prefix 在 Windows CMD 下失效
        _, stdout, stderr = run(
            "git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 push",
            cwd=git_dir
        )
        if not stderr or "Everything up-to-date" in stderr or stdout:
            print("??? 已 push 到 GitHub")
        else:
            print(f"?  push 可能失败: {stderr}")
    else:
        print("? 本地已提交但未 push。加 --push 参数推送。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步 Hermes skill 到 Git 项目")
    parser.add_argument("skill", help="skill 名称")
    parser.add_argument("--push", action="store_true", help="自动推送到 GitHub")
    args = parser.parse_args()

    sync(args.skill, args.push)
