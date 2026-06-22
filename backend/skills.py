from pathlib import Path


WORKSPACE_ROOT = Path.cwd().resolve()
SKILLS_ROOT = WORKSPACE_ROOT / "skills"


def read_text_file(path: Path) -> str:
    """
    读取文本文件，优先 utf-8，失败时尝试 gbk。
    """

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="ignore")


def list_available_skills() -> list[dict]:
    """
    列出当前项目中的所有技能包。
    每个技能包是 skills/某个名字/SKILL.md。
    """

    if not SKILLS_ROOT.exists():
        return []

    skills = []

    for skill_dir in sorted(SKILLS_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            continue

        try:
            content = read_text_file(skill_file)
        except Exception:
            content = ""

        title = skill_dir.name
        description = "暂无说明"

        for line in content.splitlines():
            line = line.strip()

            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                continue

            if line and not line.startswith("#") and description == "暂无说明":
                description = line
                break

        skills.append({
            "name": skill_dir.name,
            "title": title,
            "description": description,
            "path": f"skills/{skill_dir.name}/SKILL.md"
        })

    return skills


def load_skill(skill_name: str) -> str:
    """
    加载指定技能包的 SKILL.md 内容。
    """

    if not skill_name:
        return "缺少 skill_name 参数，请提供技能包名称。"

    # 防止路径穿越，只允许简单技能名
    if "/" in skill_name or "\\" in skill_name or ".." in skill_name:
        return "安全限制：skill_name 不能包含路径符号。"

    skill_file = SKILLS_ROOT / skill_name / "SKILL.md"

    try:
        skill_file = skill_file.resolve()

        try:
            skill_file.relative_to(SKILLS_ROOT.resolve())
        except ValueError:
            return "安全限制：不能加载 skills 目录之外的内容。"

        if not skill_file.exists():
            available = list_available_skills()
            names = [item["name"] for item in available]
            return f"技能包不存在：{skill_name}。当前可用技能包：{names}"

        content = read_text_file(skill_file)

        if not content.strip():
            return f"技能包 {skill_name} 是空的。"

        max_chars = 8000

        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n……技能内容较长，后面部分已省略。"

        return content

    except Exception as e:
        return f"load_skill 执行失败：{e}"